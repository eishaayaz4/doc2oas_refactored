#!/bin/python3
"""
Classes and functions to model the data definition
"""

from data_field import DataField

from data_field import QueryTableRow, ApiTableRow

from utils import SPC

DICT_FOR_REF_DM = {}
DICT_FOR_COUNT = {}
COUNT_DICT = {}
REF_DM_DICT = {}


def next_sibling_field_idx(tab, first_descendant_id, nesting_lvl):
    """
    Returns the index of the first sibling data field of the data field with the given ID.

    Args:
        tab (list): A list of data fields, where each entry is a tuple (field_id, field_content).
        first_descendant_id (int): The ID of the first descendant data field.
        nesting_lvl (int): The nesting level of the data fields.

    Returns:
        int: The index of the first sibling data field in the 'tab' list following the provided 'first_descendant_id'.
    
    """
    res = first_descendant_id
    prefix = ">" * (int(nesting_lvl) + 1)
    while res < len(tab) and tab[res][0].startswith(prefix):
        res = res + 1
    return res


def get_oas_enumeration_obj(tab, type_reference="", nesting=0):
    """
    Extracts OpenAPI Specification (OAS) enumeration objects from a given table.

    This function parses a table represented as a list of rows and extracts information about enumeration objects
    specified in the table, conforming to the OAS schema.

    Parameters:
    - tab (list): A list of rows representing the table containing enumeration object information.
    - type_reference (str, optional): A reference to the type or schema to which the enumeration objects belong.

    Returns:
    dict: A dictionary containing extracted enumeration objects conforming to the OAS schema.
    
    res = {}

    return res
    
    """


def get_oas_data_definition_obj_for_nested_fields(tab, type_reference="", nesting=0):
    """
    Parse a data definition table into a Python dictionary following the OpenAPI Specification (OAS) format.

    This function processes a table, represented as a list of rows, and extracts information about data model definitions.
    It creates a Python dictionary conforming to the OAS schema, which includes properties, types, descriptions,
    and nested data models.

    Parameters:
    - tab (list): A list of rows representing the data definition table.
    - type_reference (str, optional): A reference to the data model or schema to which the definitions belong.
    - nesting (int, optional): The nesting level of the data model within the table.

    Returns:
    dict: A dictionary containing the parsed data model definition conforming to the OAS schema.
    """
    res = {}
    if not nesting:
        res["x-etsi-ref"] = type_reference
        res["type"] = "object"

    required = []
    properties = {}
    notes = []

    if not tab:
        return res

    idx = 0
    while idx < len(tab):
        if "Attribute" in tab[idx][0] or tab[idx][0] == "Element":
            idx = idx + 1
            continue

        data_field = DataField(tab[idx][0], tab[idx][1], tab[idx][2], tab[idx][3])
        mydict = data_field.to_dict()

        if data_field.is_note:
            notes = mydict
            idx = idx + 1
        else:
            if data_field.has_inlined:
                nidx = next_sibling_field_idx(tab, idx + 1, nesting)
                nested_data_fields = get_oas_data_definition_obj_for_nested_fields(
                    tab[idx + 1 : nidx], type_reference="", nesting=nesting + 1
                )
                mydict.update(nested_data_fields)
                idx = nidx
            else:
                idx = idx + 1
            name_to_PascalCase = data_field.name[:1].upper() + data_field.name[1:]
            if data_field.has_inlined:
                if DICT_FOR_REF_DM:
                    try:
                        if name_to_PascalCase in DICT_FOR_REF_DM:
                            if mydict == DICT_FOR_REF_DM[name_to_PascalCase]:
                                if data_field.is_array:
                                    properties[data_field.name] = {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/" + name_to_PascalCase
                                        },
                                    }
                                    DICT_FOR_REF_DM[name_to_PascalCase] = mydict
                                else:
                                    properties[data_field.name] = {
                                        "$ref": "#/components/schemas/" + name_to_PascalCase
                                    }
                                    DICT_FOR_REF_DM[name_to_PascalCase] = mydict
                            elif mydict in [*DICT_FOR_REF_DM.values()]:
                                key = list(DICT_FOR_REF_DM.keys())[
                                    list(DICT_FOR_REF_DM.values()).index(mydict)
                                ]
                                if data_field.is_array:
                                    properties[data_field.name] = {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/" + key},
                                    }
                                    DICT_FOR_REF_DM[key] = mydict
                                else:
                                    properties[data_field.name] = {
                                        "$ref": "#/components/schemas/" + key
                                    }
                                    DICT_FOR_REF_DM[key] = mydict
                            else:
                                if name_to_PascalCase in DICT_FOR_COUNT:
                                    DICT_FOR_COUNT[name_to_PascalCase] += 1
                                else:
                                    DICT_FOR_COUNT[name_to_PascalCase] = 0
                                temp_count = DICT_FOR_COUNT[name_to_PascalCase]
                                if data_field.is_array:
                                    properties[data_field.name] = {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/"
                                            + name_to_PascalCase
                                            + str(temp_count)
                                        },
                                    }
                                    DICT_FOR_REF_DM[name_to_PascalCase + str(temp_count)] = mydict
                                else:
                                    properties[data_field.name] = {
                                        "$ref": "#/components/schemas/"
                                        + name_to_PascalCase
                                        + str(temp_count)
                                    }
                                    DICT_FOR_REF_DM[name_to_PascalCase + str(temp_count)] = mydict
                        else:
                            DICT_FOR_COUNT[name_to_PascalCase] = 0
                            if data_field.is_array:
                                properties[data_field.name] = {
                                    "type": "array",
                                    "items": {
                                        "$ref": "#/components/schemas/" + name_to_PascalCase
                                    },
                                }
                                DICT_FOR_REF_DM[name_to_PascalCase] = mydict
                            else:
                                properties[data_field.name] = {
                                    "$ref": "#/components/schemas/" + name_to_PascalCase
                                }
                                DICT_FOR_REF_DM[name_to_PascalCase] = mydict
                    except:
                        pass
                else:
                    DICT_FOR_COUNT[name_to_PascalCase] = 0
                    if data_field.is_array:
                        properties[data_field.name] = {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/" + name_to_PascalCase},
                        }
                        DICT_FOR_REF_DM[name_to_PascalCase] = mydict
                    else:
                        properties[data_field.name] = {
                            "$ref": "#/components/schemas/" + name_to_PascalCase
                        }
                        DICT_FOR_REF_DM[name_to_PascalCase] = mydict
            else:
                # Modified: Preserve all fields except 'type' when '$ref' is present
                if "$ref" in mydict:
                    # Create a new dict with all fields from mydict except 'type'
                    properties[data_field.name] = {
                        k: v for k, v in mydict.items() if k != "type"
                    }
                else:
                    properties[data_field.name] = mydict

        if data_field.is_required:
            required.append(data_field.name)

    if properties:
        res["properties"] = properties
    if required:
        res["required"] = required
    if notes:
        res["x-etsi-notes"] = notes
    return res

def get_oas_data_definition_obj(tab, type_reference="", nesting=0):
    """
    Parse a data definition table into a Python dictionary following the OpenAPI Specification (OAS) format.

    This function processes a table, represented as a list of rows, and extracts information about data model definitions.
    It creates a Python dictionary conforming to the OAS schema, which includes properties, types, descriptions,
    and nested data models.

    Parameters:
    - tab (list): A list of rows representing the data definition table.
    - type_reference (str, optional): A reference to the data model or schema to which the definitions belong.
    - nesting (int, optional): The nesting level of the data model within the table.

    Returns:
    dict: A dictionary containing the parsed data model definition conforming to the OAS schema.
    """
    res = {}
    if not nesting:
        res["x-etsi-ref"] = type_reference
        res["type"] = "object"

    required = []
    properties = {}
    notes = []

    if not tab:
        return res

    idx = 0
    while idx < len(tab):
        if "Attribute" in tab[idx][0] or tab[idx][0] == "Element":
            idx = idx + 1
            continue

        data_field = DataField(tab[idx][0], tab[idx][1], tab[idx][2], tab[idx][3])
        mydict = data_field.to_dict()

        if data_field.is_note:
            notes = mydict
            idx = idx + 1
        else:
            if data_field.has_inlined:
                nidx = next_sibling_field_idx(tab, idx + 1, nesting)
                nested_data_fields = get_oas_data_definition_obj_for_nested_fields(
                    tab[idx + 1 : nidx], type_reference="", nesting=nesting + 1
                )
                mydict.update(nested_data_fields)
                idx = nidx
            else:
                idx = idx + 1
            name_to_PascalCase = data_field.name[:1].upper() + data_field.name[1:]
            if data_field.has_inlined:
                if DICT_FOR_REF_DM:
                    try:
                        if name_to_PascalCase in DICT_FOR_REF_DM:
                            if mydict == DICT_FOR_REF_DM[name_to_PascalCase]:
                                if data_field.is_array:
                                    properties[data_field.name] = {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/" + name_to_PascalCase
                                        },
                                    }
                                    DICT_FOR_REF_DM[name_to_PascalCase] = mydict
                                else:
                                    properties[data_field.name] = {
                                        "$ref": "#/components/schemas/" + name_to_PascalCase
                                    }
                                    DICT_FOR_REF_DM[name_to_PascalCase] = mydict
                            elif mydict in [*DICT_FOR_REF_DM.values()]:
                                key = list(DICT_FOR_REF_DM.keys())[
                                    list(DICT_FOR_REF_DM.values()).index(mydict)
                                ]
                                if data_field.is_array:
                                    properties[data_field.name] = {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/" + key},
                                    }
                                    DICT_FOR_REF_DM[key] = mydict
                                else:
                                    properties[data_field.name] = {
                                        "$ref": "#/components/schemas/" + key
                                    }
                                    DICT_FOR_REF_DM[key] = mydict
                            else:
                                if name_to_PascalCase in DICT_FOR_COUNT:
                                    DICT_FOR_COUNT[name_to_PascalCase] += 1
                                else:
                                    DICT_FOR_COUNT[name_to_PascalCase] = 0
                                temp_count = DICT_FOR_COUNT[name_to_PascalCase]
                                if data_field.is_array:
                                    properties[data_field.name] = {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/"
                                            + name_to_PascalCase
                                            + str(temp_count)
                                        },
                                    }
                                    DICT_FOR_REF_DM[name_to_PascalCase + str(temp_count)] = mydict
                                else:
                                    properties[data_field.name] = {
                                        "$ref": "#/components/schemas/"
                                        + name_to_PascalCase
                                        + str(temp_count)
                                    }
                                    DICT_FOR_REF_DM[name_to_PascalCase + str(temp_count)] = mydict
                        else:
                            DICT_FOR_COUNT[name_to_PascalCase] = 0
                            if data_field.is_array:
                                properties[data_field.name] = {
                                    "type": "array",
                                    "items": {
                                        "$ref": "#/components/schemas/" + name_to_PascalCase
                                    },
                                }
                                DICT_FOR_REF_DM[name_to_PascalCase] = mydict
                            else:
                                properties[data_field.name] = {
                                    "$ref": "#/components/schemas/" + name_to_PascalCase
                                }
                                DICT_FOR_REF_DM[name_to_PascalCase] = mydict
                    except:
                        pass
                else:
                    DICT_FOR_COUNT[name_to_PascalCase] = 0
                    if data_field.is_array:
                        properties[data_field.name] = {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/" + name_to_PascalCase},
                        }
                        DICT_FOR_REF_DM[name_to_PascalCase] = mydict
                    else:
                        properties[data_field.name] = {
                            "$ref": "#/components/schemas/" + name_to_PascalCase
                        }
                        DICT_FOR_REF_DM[name_to_PascalCase] = mydict
            else:
                # Modified: Preserve all fields except 'type' when '$ref' is present
                if "$ref" in mydict:
                    # Create a new dict with all fields from mydict except 'type'
                    properties[data_field.name] = {
                        k: v for k, v in mydict.items() if k != "type"
                    }
                else:
                    properties[data_field.name] = mydict

        if data_field.is_required:
            required.append(data_field.name)

    if properties:
        res["properties"] = properties
    if required:
        res["required"] = required
    if notes:
        formatted_notes = f"|-\n  {notes.strip()}"
        res["description"] = formatted_notes
    return res

def write_oas_table_to_file(tab, type_name_clean, type_reference, buf, lvl):
    """
    Write the content of a table to a file in UTF-8 encoding.

    This function takes a table (represented as a list of rows), type name, type reference,
    file buffer, and indentation level as input and writes the table content to a file in UTF-8 encoding.
    The resulting content follows a specific format where the table represents properties of an object type
    in the OpenAPI Specification (OAS).

    Parameters:
    - tab (list): A list of rows representing the table to be written to the file.
    - type_name_clean (str): Cleaned type name.
    - type_reference (str): Type reference.
    - buf (file buffer): The buffer used for writing to the file.
    - lvl (int): Indentation level for formatting.

    The function writes the table content in the following format:
    ```
      type_name_clean: # type_reference
        type: object
        properties:
          property1:
            # Property description and details
          property2:
            # Property description and details
          ...
    ```

    Example Usage:
    To write a table 'tab' to a file, you can call this function as follows:
    write_oas_table_to_file(tab, "TypeName", "TypeReference", file_buffer, 2)
    This will write the formatted table content to the specified file buffer.

    Note:
    - The 'tab' parameter should be a table where each row represents a property of an object type.
    - The 'lvl' parameter controls the indentation level for formatting.

    Warning:
    - Ensure that the 'buf' parameter is correctly initialized and opened for writing before calling this function.
    - The function does not handle file opening or closing; it assumes the 'buf' is ready for writing.
    """

    buf.write((SPC * 2) + type_name_clean + ": # " + type_reference + "\n")
    buf.write((SPC * 3) + "type: object\n")
    buf.write((SPC * 3) + "properties:\n")

    for row in tab:
        name = row[0]
        literal_type = row[1]
        cardinality = row[2]
        description = row[3]

        data_field = DataField(name, literal_type, cardinality, description)
        #  need to know if we are in inlined situation
        txt = data_field.to_string_at_level(lvl)
        buf.write(txt)

    if not txt.endswith("\n"):
        buf.write("\n")
    buf.write("\n")


########### Functions related to API Definitions implementation #################
#################################################################################


def get_oas_for_query_param_data_definition(tab, bool_to_make_dict_empty):
    """
    Parse a data definition table into an OpenAPI Specification (OAS) compatible dictionary for query parameters.

    This function takes a data definition table and a boolean flag as input and returns an OAS compatible dictionary
    representing query parameters. The resulting dictionary can be used to define query parameters in an OAS document.

    Parameters:
    - tab (list): A list representing the data definition table to be parsed.
    - bool_to_make_dict_empty (bool): A boolean flag to indicate whether to clear the global reference dictionary.

    Returns:
    - dict: An OAS compatible dictionary representing query parameters.

    Global Variables:
    - REF_DM_DICT (dict): A global dictionary used to keep track of the current state of the result dictionary across iterations.
    - COUNT_DICT (dict): A global dictionary used to count the occurrences of distinct query parameters.

    The function iterates through the input table rows and converts them into a dictionary format suitable for OAS.
    It handles cases where query parameters have the same name by appending an integer to the parameter name to ensure uniqueness.

    Example Usage:
    To parse a data definition table 'tab' into an OAS compatible query parameter dictionary, you can call this function as follows:
    get_oas_for_query_param_data_definition(tab, True)
    This will return the OAS compatible query parameter dictionary.

    Note:
    - The 'tab' parameter should be a table where each row represents a query parameter definition.
    - The 'bool_to_make_dict_empty' flag indicates whether to clear the global reference dictionary before processing.
    - The function utilizes global variables 'REF_DM_DICT' and 'COUNT_DICT' to maintain state across iterations.
    - Ensure that the global reference dictionaries are initialized as needed before calling this function.
    """
    global REF_DM_DICT
    if bool_to_make_dict_empty == True:
        REF_DM_DICT = {}
    list_to_dict = {}
    parameters = {}
    mydict = {}

    data_field = {}
    if not tab:
        return list_to_dict

    idx = 0
    while idx < len(tab):
        # TableRow class contains data of each row of a table.
        # in iterative manner, each element of a row is passed to TableRow class to assign a corresponding key
        try:
            data_field = QueryTableRow(
                tab[idx][0], tab[idx][1], tab[idx][2], tab[idx][3]
            )
        except:
            data_field = QueryTableRow(tab[idx][0], tab[idx][1], tab[idx][2])

        # data_field.to_dict_for_api_def() converts the python class data to python dictionary
        mydict = data_field.to_dict_for_query_param_def()

        if data_field.is_note:
            idx = idx + 1
        else:
            idx = idx + 1
            queryParam = data_field.name

            # global variable REF_DM_DICT is used to keep track of the current state of list_to_dict across iterations
            if REF_DM_DICT:
                try:
                    if queryParam in REF_DM_DICT:
                        # to check if query parameter already exist in the dictionary
                        if mydict[queryParam] == REF_DM_DICT[queryParam]:
                            print("query parameter already exists")
                        else:
                            # dictionary to hold a count for number of distinct query parameters with same name
                            if queryParam in COUNT_DICT:
                                COUNT_DICT[queryParam] += 1
                            else:
                                COUNT_DICT[queryParam] = 0
                            # the temp-count will be used to append an integer at the end of query name in case of multiple occurences
                            temp_count = COUNT_DICT[queryParam]
                            mydict[queryParam]["x-exportParamName"] = queryParam + str(
                                temp_count
                            )
                            REF_DM_DICT[queryParam + str(temp_count)] = mydict.pop(
                                list(mydict.keys())[0]
                            )
                            parameters[queryParam + str(temp_count)] = REF_DM_DICT[
                                queryParam + str(temp_count)
                            ]
                    else:
                        COUNT_DICT[queryParam] = 0
                        REF_DM_DICT[queryParam] = mydict.pop(list(mydict.keys())[0])
                        parameters[queryParam] = REF_DM_DICT[queryParam]
                except:
                    pass
            else:
                COUNT_DICT[queryParam] = 0
                REF_DM_DICT = mydict
                parameters = REF_DM_DICT

    if parameters:
        list_to_dict.update(parameters)

    return list_to_dict


def get_oas_for_api_data_definition(tab, config):
    """
    Parse a data definition table into Python dictionaries for API definition.

    This function takes a data definition table and converts it into two Python dictionaries representing API definitions.
    
    Parameters:
    - tab (list): A matrix of strings representing the table data.

    Returns:
    - tuple: A tuple containing two dictionaries: list_to_dict and list_to_dict1.
      - list_to_dict (dict): A dictionary representing API definitions with endpoints and methods.
      - list_to_dict1 (dict): A dictionary representing the request schema for API definitions.

    The function iterates through the input table rows and converts them into dictionaries suitable for API definitions.
    It distinguishes between endpoint and method definitions and combines them into the final API definition dictionary.
    Additionally, it extracts the request schema from the input table and populates list_to_dict1 with it.

    Example Usage:
    To parse a data definition table 'tab' into two dictionaries representing API definitions, you can call this function as follows:
    result_tuple = get_oas_for_api_data_definition(tab)
    This will return a tuple containing two dictionaries: list_to_dict and list_to_dict1.

    Note:
    - The 'tab' parameter should be a table where each row represents an API definition.
    - The function distinguishes between endpoint and method definitions based on the structure of the input table.
    - It populates list_to_dict with the combined API definitions and list_to_dict1 with the request schema.
    - The resulting dictionaries can be used for further processing or generation of API documentation.
    """
    list_to_dict = {}
    mydict = {}
    list_to_dict1 = {}
    data_field = {}

    # If tab is empty, return an empty dictionary
    if not tab:
        return list_to_dict

    idx = 0

    while idx < len(tab):
        # Create an ApiTableRow object with the data in the current row
        data_field = ApiTableRow(tab[idx][0], tab[idx][1], tab[idx][2], tab[idx][3])

        # Convert the ApiTableRow object to a dictionary suitable for API definition
        mydict = data_field.to_dict_for_api_def(config)
        # Merges the request schema dictionary from mydict into list_to_dict1
        if idx == 0:
            list_to_dict1.update(mydict[1])

        # Ignore if mydict is empty i.e. the row has a Note
        if list(mydict[0].keys()):
            key_value = list(mydict[0].keys())[0]
        else:
            # Move to the next row if the current row has a Note
            idx = idx + 1
            continue
        # Get the method key value from the dictionary
        method_key_value = list(mydict[0][key_value].keys())[0]

        # Update the list_to_dict dictionary with the data in the current row
        if key_value in list_to_dict:
            if not method_key_value in list_to_dict[key_value]:
                list_to_dict[key_value][method_key_value] = mydict[0][key_value][
                    method_key_value
                ]
        else:
            list_to_dict[key_value] = mydict[0][key_value]
        idx = idx + 1
    return list_to_dict, list_to_dict1
