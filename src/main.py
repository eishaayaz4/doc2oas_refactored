#!/bin/python3
"""
Generate openapi definitions from Docx specification
"""

import sys
import os
from io import StringIO
import logging
import yaml
from collections import Counter
import docx
from docx.table import Table
from docx.text.paragraph import Paragraph
from copy import deepcopy
import copy
import re

from data_definition import get_oas_data_definition_obj
from data_definition import (
    get_oas_for_query_param_data_definition,
    get_oas_for_api_data_definition,
)
from data_definition import get_oas_enumeration_obj
from utils import (
    docx_tab_to_string_matrix,
    get_content,
    find_all_sections,
    yaml_dump,
    docx_tab_to_string_matrix_for_query_param_def,
    docx_tab_to_string_matrix_for_api_def,
    populate_callbacks,
)
import json
from data_definition import DICT_FOR_REF_DM

MODELS = {}
OAS_DICT = {}
config = {}
new_data_models = set()
sum_dict = None

OAS_DICT["openapi"] = "3.1.0"
OAS_DICT["jsonSchemaDialect"] = "https://json-schema.org/draft/2020-12/schema"
OAS_DICT["info"] = {}
OAS_DICT["servers"] = {}
OAS_DICT["paths"] = {}
OAS_DICT["components"] = {"schemas": {}}
OAS_DICT["components"]["responses"] = {}
OAS_DICT["components"]["parameters"] = {}


def add_fake_datatype(a, b):
    a["components"]["schemas"][b] = {"type": "string"}


def add_manual_datatype(a, b, c):
    a["components"]["schemas"][b] = c


FAKE_DATA_TYPES = [
    "Not_specified",
    "CategoryRef",
    "String",
    "SecurityInfo",
    "ChangeAppInstanceStateOpConfig",
    "SwImageDescriptor",
    "TerminateAppInstanceOpConfig",
    "VirtualComputeDescription",
    "VirtualStorageDescriptor",
    "URI",
    "Enum_inlined",
    "AppPkgArtifactInfo",
    "Checksum",
    "AppPkgSWImageInfo",
    "AppInstanceSubscriptionFilter",
]


def is_api_data_model_def(table):
    """
    Check if a table contains an API data model definition.

    This function checks whether a given table conforms to the format of an API data model definition table. 
    An API data model definition table is expected to have four columns (with an exception for a five-column table with the 'Cardinality' column repeated), 
    with specific headers in the following order:
    - "Attribute name"
    - "Data type"
    - "Cardinality"
    - "Description"

    Parameters:
    - table (object): The table to be checked, typically represented as an object in the document.

    Returns:
    - bool: True if the table is an API data model definition, False otherwise.

    The function compares the labels of the table's columns with the expected headers. If the labels match any of the expected patterns, 
    the function returns True, indicating that the table represents an API data model definition.

    Example Usage:
    To determine if a given table 'my_table' is an API data model definition, you can call this function as follows:
    result = is_api_data_model_def(my_table)
    This will return True if 'my_table' is a valid API data model definition table and False otherwise.
    """

    expected_labels = ["Attribute name", "Data type", "Cardinality", "Description"]

    # Workaround needed as some tables in the document do not comply with the format
    expected_labels_v2 = [
        "Attribute name",
        "Data type",
        "Cardinality",
        "Cardinality",
        "Description",
    ]

    # Workaround needed as some tables in the document do not comply with the format
    expected_labels_v3 = ["Attribute", "Data type", "Cardinality", "Description"]

    # Workaround needed as some tables in the document do not comply with the format
    expected_labels_v4 = ["Element", "Type", "Cardinality", "Description"]

    # Workaround needed as some tables in the document do not comply with the format
    expected_labels_v5 = ["Name", "Data type", "Cardinality", "Remarks"]

    labels = [table.columns[i].cells[0].text for i in range(len(table.columns))]

    if not labels == expected_labels and labels == expected_labels_v2:
        logging.debug("LABELS: [%s]", ",".join(labels))

    return (
        (len(table.columns) == 4 and labels == expected_labels)
        or (len(table.columns) == 5 and labels == expected_labels_v2)
        or (len(table.columns) == 4 and labels == expected_labels_v3)
        or (len(table.columns) == 4 and labels == expected_labels_v4)
        or (len(table.columns) == 4 and labels == expected_labels_v5)
    )


def is_api_data_model_def_of_mec_010(table):
    """
    Check if a table conforms to the format of an API data model definition for MEC-010.

    This function checks whether a given table is formatted as an API data model definition for the MEC-010 specification.
    An MEC-010 API data model definition table is expected to have four columns (with an exception for a five-column table with the 'Cardinality' column repeated), 
    with specific headers in the following order:
    - "Attribute name"
    - "Cardinality"
    - "Data type"
    - "Description"

    Parameters:
    - table (object): The table to be checked, typically represented as an object in the document.

    Returns:
    - bool: True if the table is an MEC-010 API data model definition, False otherwise.

    The function extracts the labels from the table's columns and compares them with the expected headers for MEC-010 API data model definitions. 
    If the labels match the expected pattern and the table has four columns, the function returns True, indicating that the table represents an MEC-010 API data model definition.

    Example Usage:
    To determine if a given table 'my_table' is an MEC-010 API data model definition, you can call this function as follows:
    result = is_api_data_model_def_of_mec_010(my_table)
    This will return True if 'my_table' is a valid MEC-010 API data model definition table and False otherwise.
    """

    expected_labels_mec = ["Attribute name", "Cardinality", "Data type", "Description"]

    labels = [table.columns[i].cells[0].text.strip().replace("\n", " ") for i in range(len(table.columns))]

    return len(table.columns) == 4 and labels == expected_labels_mec


def oas_output_info(name, imports):
    """
    Generate OAS Output Information for an API Definition.

    This function generates and returns a dictionary that contains information about the output of an OpenAPI Specification (OAS) file for an API definition.

    Parameters:
    - name (str): The name of the OAS output.
    - imports (list): A list of import statements or dependencies related to the API definition.

    Returns:
    - dict: A dictionary containing the following fields:
        - "name" (str): The name of the OAS output.
        - "fn" (str): The filename associated with the OAS output, typically in YAML format.
        - "fd" (None): A placeholder for file descriptor (not used in this function).
        - "imports" (list): A list of import statements or dependencies related to the API definition.
        - "buf" (StringIO): A StringIO buffer for storing the OAS content.

    The function is used to initialize information about the OAS output, including its name, filename, imports, and a buffer for OAS content storage.

    Example Usage:
    To create an OAS output information object for an API definition named "my_api" with specific imports, you can call this function as follows:
    oas_info = oas_output_info("my_api", ["import1", "import2"])
    This will return a dictionary containing the OAS output information that can be used in the API definition process.

    Note:
    This function is typically used in conjunction with other functions and data structures for generating and managing OAS content.
    """
    return {
        "name": name + ".yaml",
        "fn": "{}.yaml".format(name),
        "fd": None,
        "imports": imports,
        "buf": StringIO(),
    }


MODELS = {}


# Parent class of DataType() class
class DataModel:
    """
    Represents a data model within the documentation. A data model consists of a type name,
    type name clean, and type reference, as well as a data definition.

    Attributes:
    - type_name (str): The raw type name extracted from the document.
    - type_name_clean (str): A cleaned version of the type name without any prefixes or extra characters.
    - type_reference (str): A reference associated with the data model.
    - data_definition (dict): A dictionary representing the data definition of the data model.

    Methods:
    - parse_data_definition(string_matrix): Parses the data definition from a string matrix
      and returns it as a dictionary.
    - parse_table_elem(elem, reverse_order=False): Parses the data model's table element
      and returns the data definition.
    """
    def __init__(self, elem):
        """
        Initializes a DataModel instance.

        Parameters:
        - elem (str or Element): The element representing the data model.
        """
        if isinstance(elem, str):
            self.type_name = elem
            self.type_name_clean = elem
            self.type_reference = "A.V.D"
        else:
            self.type_name = elem.text
            self.type_name_clean = self.type_name.split(":")[1][1:].strip()
            self.type_reference = self.type_name.split("T")[0].strip()

        logging.debug(
            "-- TYPE HEADING: " + self.type_reference + " " + self.type_name_clean
        )
        self.data_definition = {}

    def parse_data_definition(self, string_matrix):
        # raise UnimplementedError("Unimplemented")
        return {}

    def parse_table_elem(self, elem, reverse_order=False):
        """
        Parses the data model's table element and returns the data definition.

        This method extracts the data definition from a table element representing
        the structure of the data model. It logs information about the table and
        then processes it to create the data definition dictionary.

        Parameters:
        - elem (Element): The table element representing the data definition.
        - reverse_order (bool, optional): Whether to reverse the order of table rows.
        Default is False.

        Returns:
        - dict: A dictionary representing the parsed data definition.

        Example:
        ```
        data_model = DataModel(elem)
        data_definition = data_model.parse_table_elem(table_elem)
        ```

        Note:
        - The `elem` parameter should be a valid Element containing the data model's table.
        - Setting `reverse_order` to True can be useful when tables have reversed row order.
        """
        logging.debug(
            "---- TYPE TABLE: " + self.type_reference + " " + self.type_name_clean
        )
        # docx_tab_to_string_matrix converts the Table into array of strings, [1:] to ignore first row of the table
        string_matrix = docx_tab_to_string_matrix(elem, reverse_order)[1:]
        self.data_definition = self.parse_data_definition(string_matrix)
        return self.data_definition


class DataType(DataModel):
    """
    Represents a data type definition within an API specification.

    This class extends the functionality of the base DataModel class to specifically
    handle data type definitions. It parses and stores information about the data type
    and its structure.

    Parameters:
    - elem (str or Element): The element or name of the data type.

    Attributes:
    - type (str): The type of data, which is set to "type" for data type definitions.

    Methods:
    - parse_data_definition(string_matrix): Parses the data type's definition from a
      string matrix and returns it as an OpenAPI Specification (OAS) compatible dictionary.

    Example:
    ```
    data_type_elem = "DataType: User"
    data_type = DataType(data_type_elem)
    data_definition = data_type.parse_data_definition(data_matrix)
    ```

    Note:
    - The `elem` parameter can be either a string or an Element representing the data type.
    """
    def __init__(self, elem):
        DataModel.__init__(self, elem)
        self.type = "type"

    def parse_data_definition(self, string_matrix):
        """
        Parses the data type's definition from a string matrix.

        This method takes a string matrix representing the data type's structure and
        returns it as an OpenAPI Specification (OAS) compatible dictionary.

        Parameters:
        - string_matrix (list of list of str): The string matrix containing the data type's
          structure.

        Returns:
        - dict: An OAS compatible dictionary representing the parsed data type definition.

        Example:
        ```
        data_matrix = [["Attribute name", "Data type", "Cardinality", "Description"],
                       ["name", "string", "1", "The user's name"],
                       ["age", "integer", "1", "The user's age"]]
        data_type = DataType("DataType: User")
        data_definition = data_type.parse_data_definition(data_matrix)
        ```

        Note:
        - The `string_matrix` parameter should be a list of lists where each inner list
          represents a row of the data type's structure.
        - This method is used to extract and parse data type definitions from tables.
        """
        return get_oas_data_definition_obj(
            string_matrix, type_reference=self.type_reference, nesting=0
        )


class DataEnumeration(DataModel):
    """
    Represents an enumeration data type within an API specification.

    This class extends the functionality of the base DataModel class to specifically
    handle enumeration data type definitions. It parses and stores information about the
    enumeration type and its values.

    Parameters:
    - elem (str or Element): The element or name of the enumeration data type.

    Attributes:
    - type (str): The type of data, which is set to "enumeration" for enumeration data types.

    Methods:
    - parse_data_definition(string_matrix): Parses the enumeration data type's definition
      from a string matrix and returns it as an OpenAPI Specification (OAS) compatible dictionary.

    Example:
    ```
    enumeration_elem = "Enumeration: Gender"
    enumeration_type = DataEnumeration(enumeration_elem)
    enumeration_definition = enumeration_type.parse_data_definition(enum_matrix)
    ```

    Note:
    - The `elem` parameter can be either a string or an Element representing the enumeration data type.
    """
    def __init__(self, elem):
        DataModel.__init__(self, elem)
        self.type = "enumeration"

    def parse_data_definition(self, string_matrix):
        """
        Parses the enumeration data type's definition from a string matrix.

        This method takes a string matrix representing the enumeration data type's structure
        and returns it as an OpenAPI Specification (OAS) compatible dictionary.

        Parameters:
        - string_matrix (list of list of str): The string matrix containing the enumeration data
          type's structure.

        Returns:
        - dict: An OAS compatible dictionary representing the parsed enumeration data type definition.

        Example:
        ```
        enum_matrix = [["Value", "Description"],
                       ["male", "Male gender"],
                       ["female", "Female gender"]]
        enumeration_type = DataEnumeration("Enumeration: Gender")
        enumeration_definition = enumeration_type.parse_data_definition(enum_matrix)
        ```

        Note:
        - The `string_matrix` parameter should be a list of lists where each inner list represents
          a row of the enumeration data type's structure.
        - This method is used to extract and parse enumeration data type definitions from tables.
        """
        # get_oas_data_definition method takes string_matrix as input and returns it as an OAS compatible dictionary.
        return get_oas_enumeration_obj(
            string_matrix, type_reference=self.type_reference, nesting=0
        )


FAKE_DATA_TYPES_COUNT = 0
subscription_types = []


def generate_data_models_tables_between(a_id, b_id, content, schemas_dict):
    """
    Loops over content to extract and generate JSON schemas for data models and enumerations
    between the specified indices [a_id, b_id) and writes them to the 'schemas_dict'.

    This function iterates over a portion of the content and identifies data models and enumerations
    based on specific patterns in the document. It then generates JSON schemas for these data models
    and enumerations and stores them in the provided 'schemas_dict' dictionary.

    Parameters:
    - a_id (int): The starting index for iterating over the 'content'.
    - b_id (int): The ending index (exclusive) for iterating over the 'content'.
    - content (list): A list containing document elements (e.g., paragraphs, tables) to be processed.
    - schemas_dict (dict): A dictionary to store the generated JSON schemas, where keys are data model
      or enumeration names, and values are the corresponding JSON schemas.

    Returns:
    - int: The number of JSON schema definitions generated and added to 'schemas_dict'.

    Example:
    ```
    # Extract data models and enumerations between indices 10 and 20 in 'content'
    start_idx = 10
    end_idx = 20
    schema_definitions = {}
    generated_count = generate_data_models_tables_between(start_idx, end_idx, content, schema_definitions)
    ```

    Note:
    - Data models and enumerations are identified based on patterns in the document content.
    - The function relies on specific formatting patterns and table structures to recognize and
      generate JSON schemas.
    - The generated JSON schemas are stored in 'schemas_dict' for further use.
    """
    global FAKE_DATA_TYPES_COUNT
    definitions_count = 0

    type_name = "NOT SET"
    type_name_clean = "NOT SET"
    type_reference = "NOT SET"

    ndm = None
    for idx in range(a_id, b_id):
        if idx < len(content):
            # In iterative manner each element between the given index will be assigned to tmp_elem
            tmp_elem = content[idx]
            # condition to check if the element from the content is 'paragraph' and 'Type: '
            if isinstance(tmp_elem, Paragraph) and "Type: " in tmp_elem.text.replace(
                "\t", " "
            ):
                ndm = DataType(tmp_elem)
                definitions_count = definitions_count + 1

            # condition to check if the element from the content is 'paragraph' and 'Enumeration: '
            if isinstance(tmp_elem, Paragraph) and "Enumeration: " in tmp_elem.text:
                ndm = DataEnumeration(tmp_elem)
                definitions_count = definitions_count + 1

            # is_api_data_model_def function checks the first row of the data model table and return True if it finds a match in the lists defined in it
            if isinstance(tmp_elem, Table) and is_api_data_model_def(tmp_elem):
                if not ndm:
                    FAKE_DATA_TYPES_COUNT = FAKE_DATA_TYPES_COUNT + 1
                    ndm = DataType("Fake Data Type " + str(FAKE_DATA_TYPES_COUNT))
                # pass the fetched Table to parse_table_elem function of class DataModel, using ndm
                # parse_table_elem returns all elements in the data model table as a python object in OAS format
                schemas_dict[ndm.type_name_clean] = ndm.parse_table_elem(tmp_elem)

            # is_api_data_model_def_of_mec_010 function checks the first row of the data model table and return True if it finds a match in the lists defined in it
            if isinstance(tmp_elem, Table) and is_api_data_model_def_of_mec_010(
                tmp_elem
            ):
                if not ndm:
                    FAKE_DATA_TYPES_COUNT = FAKE_DATA_TYPES_COUNT + 1
                    ndm = DataType("Fake Data Type " + str(FAKE_DATA_TYPES_COUNT))
                schemas_dict[ndm.type_name_clean] = ndm.parse_table_elem(tmp_elem, True)
        else:
            logging.debug(
                "idx >=len(content): A=%s, B: %s, IDX: %s, len(content): %s",
                a_id,
                b_id,
                idx,
                len(content),
            )
            break

    return definitions_count


def generate_data_models_tables_for(section, content, schemas_dict):
    """
    Generates data models from tables for a specific section and adds them to schemas_dict.

    Args:
        section (Section): The section object that defines the range of content to process.
        content (list): A list of elements (e.g., paragraphs, tables) containing the content to parse.
        schemas_dict (dict): A dictionary to store the generated data models in OpenAPI Schema format.

    Returns:
        int: The number of data models generated and added to schemas_dict.
    """
    # function which performs conversion of data models from docx to OAS schemas by looping elements in the content variable between the given indexes
    return generate_data_models_tables_between(
        section.id_from, section.id_to, content, schemas_dict
    )


class API:
    def __init__(self):
        pass


def generate_oas(filename, headings):
    """
    Takes a filename or file object and loads the definition into the MODELS dictionary.

    Args:
        filename (str or file object): The filename or file object of the Docx document to process.
        headings (list of str): A list of section headings that define where data models are located within the document.

    Raises:
        ValueError: If the provided Docx file cannot be opened or if no recognized data models sections are found.

    Notes:
        This function loads data models from specified sections in the Docx document and stores them in the MODELS dictionary.
    """
    try:
        logging.info("Opening %s", filename)
        api_spec = docx.Document(filename)
    except:
        logging.critical("Error opening the submitted Docx file")
        raise ValueError("Cannot open the submitted Docx file")

    # get_content will return an array of all paragraphs and tables
    content = get_content(api_spec)
    logging.info("Searching clauses:")
    logging.info(headings)
    # find_all_sections will return start and end index of Data Model heading by searching in content
    sections = find_all_sections([headings], content)

    print(sections)

    if len(sections) == 0:
        logging.critical(
            "Could not find any of the sections configured. Make sure that the names of the clause containing the data models are correctly configured."
        )
        raise ValueError("No data models section recognized.")

    # logic to get version of specification document from its title and assign version value to 'version' under 'info' section in OAS_DICT
    title_sentence = content[0].text
    clean_sentence = title_sentence.strip().split(" ")
    for word in clean_sentence:
        if word[0] == "V":
            OAS_DICT["info"]["version"] = word[1:]

    for section in sections:
        count = generate_data_models_tables_for(
            section, content, OAS_DICT["components"]["schemas"]
        )
        logging.info("Printed %d types to '%s'\n", count, section.heading)


def is_a_map_value(entry_name):
    """
    Checks if a given entry name represents a map (key-value pair) in the context of data modeling.

    Args:
        entry_name (str): The name of the entry to check.

    Returns:
        bool: True if the entry represents a map, False otherwise.

    Notes:
        In data modeling, a map typically refers to a structure that stores key-value pairs, such as a dictionary or mapping.
        This function is used to determine if a given entry name corresponds to such a map structure.
    """
    return entry_name == "KeyValuePair" or entry_name == "KeyValuePairs"


###E.g. input_str = map(MyCustomObject) return the string "MyCustomObject"


def get_map_object_value(input_str):
    """
    Extracts the value inside a 'map(...)' declaration from a given input string.

    Args:
        input_str (str): The input string containing a 'map(...)' declaration.

    Returns:
        str: The value inside the 'map(...)' declaration.

    Example:
        If the input_str is "map(int,string)", this function will return "int,string".

    Notes:
        This function is used to extract the content of a 'map(...)' declaration commonly found in data modeling contexts.
    """
    str_tmp = input_str.find("map(")
    str_tmp = input_str[str_tmp : len(input_str)]
    str_tmp = str_tmp.split("(")[1]
    str_tmp = str_tmp.split(")")[0]
    return str_tmp


def update_key_value_pair_entries():
    """
    Updates properties with 'KeyValuePair' or 'KeyValuePairs' values to use '$ref' in the OpenAPI specification.

    This function iterates through the components of the OpenAPI specification and checks for properties with types 'KeyValuePair' or 'KeyValuePairs'. If found, it replaces the property with a '$ref' reference to the corresponding schema definition.

    Returns:
        set: A set containing the names of components that reference 'KeyValuePair' or 'KeyValuePairs' schemas.

    Example:
        Suppose a component 'MyComponent' has a property 'myProperty' with type 'KeyValuePair'. This function will update 'myProperty' to use '$ref' to reference the 'KeyValuePair' schema, and the returned set will contain 'KeyValuePair'.

    Notes:
        This function is used to improve the structure and reusability of schema definitions by replacing properties with references to schema definitions.
    """
    components = OAS_DICT["components"]["schemas"]
    components_name = set()
    updates = []

    for component_name, component in components.items():
        if component is None:
            continue  # Skip this iteration if the component is None

        if "properties" not in component:
            # Skip component if it does not have "properties"
            continue

        properties = component["properties"]

        for property_name in properties:
            property_dict = properties[property_name]
            if property_name == "description":
                continue

            if "type" not in property_dict:
                continue

            property_type = property_dict["type"]

            if is_primitive_type(
                property_type
            ):  ##Primitive type (String, int, float and so on) cannot be map
                continue

            if property_type == "object":
                for value in property_dict.values():
                    if is_a_map_value(value):  # Object could be a keyValuePair(s)
                        ##KeyValuePair and KeyValuePairs are the same thing because of a typo in the spec.
                        components_name.add(value)
                        if value[-1] != "s":
                            updates.append(
                                [
                                    component_name,
                                    property_name,
                                    "#/components/schemas/" + value + "s",
                                ]
                            )
                        else:
                            updates.append(
                                [
                                    component_name,
                                    property_name,
                                    "#/components/schemas/" + value,
                                ]
                            )
    for update in updates:
        component_name = update[0]
        property_name = update[1]
        ref_value = update[2]
        OAS_DICT["components"]["schemas"][component_name]["properties"][
            property_name
        ] = {}
        OAS_DICT["components"]["schemas"][component_name]["properties"][property_name][
            "$ref"
        ] = ref_value
    return components_name



def add_new_str_to_obj_data_value():
    """
    Adds new object data models to the OpenAPI specification with string type values.

    This function iterates through a list of new data model names and adds them to the OpenAPI specification as object data models with string type values. The new data models are defined as objects with an 'additionalProperties' field referencing a string type.

    Example:
        Suppose the list 'new_data_models' contains ['NewModel1', 'NewModel2']. This function will add the following definitions to the OpenAPI specification:
        - 'NewModel1': {'type': 'object', 'additionalProperties': {'type': 'string'}}
        - 'NewModel2': {'type': 'object', 'additionalProperties': {'type': 'string'}}

    Notes:
        This function is used to define new data models with string type values in the OpenAPI specification.
    """
    for new_data_model in new_data_models:
        ref_to_specific_obj = {"$ref": "#/components/schemas/" + new_data_model[:-3]}
        oas_map = {"type": "object", "additionalProperties": ref_to_specific_obj}
        OAS_DICT["components"]["schemas"][new_data_model] = {}
        OAS_DICT["components"]["schemas"][new_data_model] = oas_map


def replace_str_to_object_values():
    """
    Replaces string values in the OpenAPI specification with object data model references.

    This function searches for string values in the OpenAPI specification that match the pattern 'map(...)' and replaces them with references to corresponding object data models. It identifies string values that represent map-like structures and updates them to refer to the appropriate object data model.

    Returns:
        str or int: If replacements are made, the updated OpenAPI specification as a JSON-formatted string is returned. If no replacements are made, -1 is returned.

    Notes:
        This function is used to enhance the OpenAPI specification by replacing map-like string values with structured object data models, enabling better documentation of data models and their relationships.
    """
    dict_str_format = json.dumps(OAS_DICT)
    index = dict_str_format.find("map(")
    if index == -1:
        return -1

    str_to_replace = ""
    for element in range(index, len(dict_str_format)):
        str_to_replace = str_to_replace + dict_str_format[element]
        if dict_str_format[element] == ")":
            break
    new_value = get_map_object_value(str_to_replace)
    new_value = new_value + "Map"
    new_data_models.add(new_value)
    dict_str_format = dict_str_format.replace(str_to_replace, new_value)
    return dict_str_format


def is_primitive_type(type_property):
    """
    Checks if a given type property represents a primitive data type.

    This function determines whether the provided type property is a primitive data type, such as 'string', 'integer', or 'float'. Primitive data types are basic data types that are not complex objects or structures.

    Args:
        type_property (str): The type property to be checked.

    Returns:
        bool: True if the type property is a primitive data type, otherwise False.

    Notes:
        Primitive data types are fundamental data types that do not contain nested structures or complex data models. This function is useful for identifying simple data types in an OpenAPI specification.
    """
    return (
        type_property == "string"
        or type_property == "integer"
        or type_property == "float"
    )
def add_parameters_to_endpoints_print_all_files(oas_dict, prefix=None):
    """
    Adds path parameters to endpoint definitions in the OpenAPI specification and saves the modified specification to files.

    This function enhances an OpenAPI specification by adding path parameters to the endpoint definitions. It iterates through the paths in the OpenAPI specification, identifies parameter names in the endpoint URLs, and adds them as path parameters with appropriate descriptions. The modified specification is then saved to files.

    Args:
        oas_dict (dict): The OpenAPI specification dictionary to be modified.
        prefix (str, optional): A prefix to be added to the output filenames when saving the modified specifications. Defaults to None.

    Returns:
        dict: The modified OpenAPI specification dictionary.

    Notes:
        - This function assumes that the input OpenAPI specification follows the Swagger 2.0 or OpenAPI 3.0 format.
        - Path parameters are extracted from curly braces '{}' in the endpoint URLs.
        - The added path parameters have 'in' set to 'path', 'required' set to True, and 'schema' type set to 'string'.
        - The 'description' of each added path parameter provides context about the parameter's purpose.

    Example:
        Given an input OpenAPI specification dictionary, this function can be used to add path parameters to endpoint definitions and save the modified specification to files.

    See Also:
        - `openai.openapi.utils.yaml_dump` function for YAML serialization.
    """
    # Iterate over the paths in the OAS_DICT dictionary
    for path, methods in oas_dict.get("paths", {}).items():
        # Extract parameter names from the endpoint URL using regular expressions
        parameter_names = re.findall(r'{(.*?)}', path)

        # Iterate over the HTTP methods for the endpoint
        for http_method, method_details in methods.items():
            # Check if the parameters key exists and is a list
            if "parameters" not in method_details:
                method_details["parameters"] = []

            # Iterate over the extracted parameter names
            for parameter_name in parameter_names:
                # Define the parameters to add for this parameter
                parameter_to_add = {
                    "name": parameter_name,
                    "in": "path",
                    "required": True,
                    "description": f"The unique identifier of the {parameter_name}.",
                    "schema": {
                        "type": "string"
                    }
                }

                # Add a deep copy of the parameter to the endpoint's method
                method_details["parameters"].append(copy.deepcopy(parameter_to_add))

    global MODELS
    logging.info("Printing to files...")
    
    for model_name in MODELS:
        model = MODELS[model_name]

        if prefix is not None:
            model["fn"] = os.path.join(prefix, model["name"])

        logging.info("Writing to " + model["fn"])
        model["fd"] = open(model["fn"], "w")
        model["buf"].seek(0)
        # del OAS_DICT['components']['parameters']['Query.Filter']['cardinality']
        if 'parameters' in OAS_DICT['components'].keys():
            for param_name, param_info in OAS_DICT['components']['parameters'].items():
                if 'cardinality' in param_info:
                    del param_info['cardinality']
        model["fd"].write(yaml_dump(OAS_DICT))
        model["fd"].write("\n")
        model["fd"].close()

        with open(model["fn"], "r") as file:
            filedata = file.read()
            filedata = filedata.replace("'# ", "# ")

        with open(model["fn"], "w") as file:
            file.write(filedata)


    # Return the modified OAS_DICT
    return oas_dict

########### Functions related to API Definitions implementation #################
#################################################################################


def generate_API_def_oas(filename, path_headings):
    """
    Generates API definitions from tables in specific sections of a document and adds them to an OpenAPI specification.

    This function takes a filename or file object representing a document and generates API definitions from tables within specific sections of the document. It then adds these API definitions to an OpenAPI specification (OAS) represented as a dictionary.

    Args:
        filename (str or file-like object): The filename or file object of the document to process.
        path_headings (list of str): A list of section headings within the document that contain API definitions.

    Returns:
        None

    Notes:
        - This function assumes that the input document is in .docx format.
        - The specified section headings are used to locate and extract tables containing API definitions.
        - API definitions are extracted from tables and added to the 'paths' section of the OAS.
        - The generated OAS is stored in the global `OAS_DICT` variable.

    Example:
        Given a document with sections containing API definitions and an empty `OAS_DICT`, this function can be used to populate the `OAS_DICT` with API definitions from those sections.

    See Also:
        - `generate_api_def_tables` function for generating API definitions from tables.
        - `OAS_DICT` global variable for storing the OpenAPI specification.
    """
    try:
        logging.info("Opening %s", filename)
        api_spec = docx.Document(filename)
    except:
        logging.critical("Error opening the submitted Docx file")
        raise ValueError("Cannot open the submitted Docx file")

    # get_content will return an array of all paragraphs and table
    content = get_content(api_spec)
    logging.info("Searching clauses:")
    logging.info(path_headings)

    # find_all_sections will return start and end index of Data Model heading by searching in content
    sections = find_all_sections([path_headings], content)

    print(sections)

    if len(sections) == 0:
        logging.critical(
            "Could not find any of the sections configured. Make sure that the names of the clause containing the API Definitions are correctly configured."
        )
        raise ValueError("No API Definitions sections recognized.")

    for section in sections:
        # generate_data_models_tables_for
        # count contains the number of tables in a specified section
        count = generate_api_def_tables(section, content, OAS_DICT)
        logging.info("Printed %d types to '%s'\n", count, section.heading)


def generate_api_def_tables(section, content, schemas_dict):
    """
    Generates API Definitions from tables within a specific section and adds them to schemas_dict.

    This function processes tables within a specified section of a document, generates API Definitions from these tables, and adds them to a dictionary representing OpenAPI schemas.

    Args:
        section (Section): The section object representing the document section to process.
        content (list): A list containing paragraphs and tables from the document.
        schemas_dict (dict): A dictionary representing OpenAPI schemas where the generated API Definitions will be added.

    Returns:
        int: The number of API Definitions generated and added to schemas_dict.

    Notes:
        - The function processes tables within the specified section to extract API Definitions.
        - API Definitions are converted to OpenAPI-compatible schemas and added to the schemas_dict.
        - The schemas_dict is typically stored under the 'components' section of an OpenAPI specification.

    Example:
        Given a document section containing API Definitions in tables, this function can be used to generate and add those API Definitions to an OpenAPI specification.

    See Also:
        - `generate_api_def_tables_between` function for processing tables and generating API Definitions.
    """
    generate_query_params_tables_between(
        section.id_from, section.id_to, content, schemas_dict
    )
    # actual function which performs conversion of API definitions from docx to OAS schemas by looping elements in the content variable between the given indexes
    return generate_api_def_tables_between(
        section.id_from, section.id_to, content, schemas_dict
    )


def generate_query_params_tables_between(a_id, b_id, content, schemas_dict):
    """
    Generates query parameters tables between two given indices in a content list and adds them to schemas_dict.

    This function processes a range of elements within a content list to extract and generate query parameters tables. The generated query parameters tables are added to a specified dictionary representing OpenAPI schemas.

    Args:
        a_id (int): The starting index for generating query parameters tables.
        b_id (int): The ending index for generating query parameters tables.
        content (list): A list containing elements from which the function generates query parameters tables.
        schemas_dict (dict): A dictionary representing OpenAPI schemas where the generated query parameters tables will be added.

    Returns:
        dict: A dictionary containing all the generated query parameters tables, stored under the 'components' section of OpenAPI schemas.

    Notes:
        - The function iterates through elements in the content list between the specified indices.
        - It identifies and processes tables that represent query parameters definitions.
        - Query parameters are converted to OpenAPI-compatible parameter objects and added to the schemas_dict under the 'components' section.

    Example:
        Given a content list containing tables with query parameter definitions, this function can be used to extract and generate OpenAPI-compatible query parameter objects, which are then added to an OpenAPI specification.

    See Also:
        - `GenerateOAS` class for parsing and generating OpenAPI-compatible query parameter objects.
    """

    global FAKE_DATA_TYPES_COUNT
    global all_quer_par_dict
    global bool_to_make_dict_empty
    ndm = None
    bool_to_make_dict_empty = False
    # Loop through elements in content between a_id and b_id
    for idx in range(a_id, b_id):
        if idx < len(content):
            # In iterative manner each element between the given index will be assigned to tmp_elem
            tmp_elem = content[idx]

            # Check if it is a query parameter definition table
            if isinstance(tmp_elem, Table) and is_query_param_def_table(tmp_elem):
                # Create instance of GenerateOAS class
                ndm = GenerateOAS(" ")
                # Parse the table element and generate a dictionary
                mydict = ndm.parse_query_param_table_elem(
                    tmp_elem, bool_to_make_dict_empty
                )
                # Update the schemas_dict dictionary with the generated query parameters table
                schemas_dict["components"]["parameters"].update(mydict)

    # Update the all_quer_par_dict variable with all the generated query parameter tables
    all_quer_par_dict = schemas_dict["components"]["parameters"]


def generate_api_def_tables_between(a_id, b_id, content, schemas_dict):
    """
    Loops over content and writes all API definitions to the schemas_dict.

    This function iterates through elements in the content list between the given indices and extracts API definitions. It processes API definition tables, request/response tables, and other relevant information from the content and adds them to a specified dictionary representing OpenAPI schemas.

    Args:
        a_id (int): The starting index for extracting API definitions.
        b_id (int): The ending index for extracting API definitions.
        content (list): A list containing elements from which API definitions are extracted.
        schemas_dict (dict): A dictionary representing OpenAPI schemas where the extracted API definitions will be added.

    Returns:
        int: The number of API definitions processed and added to the schemas_dict.

    Notes:
        - The function processes API definition tables, request/response tables, and other elements to extract API definitions.
        - It constructs OpenAPI-compatible representations of API paths, methods, parameters, and responses and adds them to the schemas_dict.
        - Callbacks and subscriptions are also handled, and relevant information is incorporated into the schemas_dict.

    Example:
        Given a content list containing API definitions and related information, this function can be used to extract and generate OpenAPI-compatible representations of API endpoints and add them to an OpenAPI specification.

    See Also:
        - `GenerateOAS` class for parsing and generating OpenAPI-compatible representations of API endpoints.
    """
    global FAKE_DATA_TYPES_COUNT
    definitions_count = 0
    global sum_dict
    ndm = None
    sec_endpoint = {}
    endpointName = ""
    dict_temp = {}

    for idx in range(a_id, b_id):
        if idx < len(content):
            # In iterative manner each element between the given index will be assigned to tmp_elem
            tmp_elem = content[idx]

            # Check if the element is an API definition overview table.
            if isinstance(tmp_elem, Table) and is_api_def_overview_table(tmp_elem):
                ndm = GenerateOAS(" ")
                # Extract the information from the table and store it in a dictionary.
                sum_dict = docx_tab_to_string_matrix_for_api_def(tmp_elem)[1:]

            if isinstance(tmp_elem, Paragraph):
                if "resource: notification endpoint" in tmp_elem.text.lower():
                    endpointName = "/user_defined_notification"
            if isinstance(tmp_elem, Paragraph) and any(
                s in tmp_elem.text.replace("\t", " ")
                for s in ("Resource URI: ", "Resource URL: ")
            ):
                ndm = GenerateOAS(tmp_elem)
                # Extract the endpoint name from the paragraph.
                endpointName = ndm.endpoint_clean
                if ("client provided" in endpointName) or (
                    "Client provided" in endpointName
                ):
                    endpointName = "/user_defined_notification"
                
                if any(s in content[idx-1].text.replace("\t", " ") for s in ("Resource URI: ", "Resource URL: ")):
                    ndm = GenerateOAS(content[idx-1])
                    sec_endpoint = ndm.endpoint_clean
                    schemas_dict["paths"].update([(sec_endpoint, "test")])           

                # Create a new temporary dictionary to store the API schema
                dict_temp = {}

            if isinstance(tmp_elem, Paragraph) and tmp_elem.text.endswith(
                ("GET", "POST", "PUT", "PATCH", "DELETE")
            ):
                description = content[idx + 1].text
                # Check if the endpoint has already been added to the dictionary.
                if endpointName not in dict_temp:
                    dict_temp[endpointName] = {}

                if (
                    "Not supported." in description
                    or "Not applicable." in description
                    or "Not Supported." in description
                    or "not supported." in description
                    or "none supported" in description
                ):
                    pass
                else:
                    # Check which HTTP method exists in paragraph.
                    if tmp_elem.text.__contains__("GET"):
                        dict_temp[endpointName]["get"] = {}
                        method_name = "get"
                    if tmp_elem.text.__contains__("PUT"):
                        dict_temp[endpointName]["put"] = {}
                        method_name = "put"
                    if tmp_elem.text.__contains__("POST"):
                        dict_temp[endpointName]["post"] = {}
                        method_name = "post"
                    if tmp_elem.text.__contains__("PATCH"):
                        dict_temp[endpointName]["patch"] = {}
                        method_name = "patch"
                    if tmp_elem.text.__contains__("DELETE"):
                        dict_temp[endpointName]["delete"] = {}
                        method_name = "delete"
                    # Extract the summary of the API endpoint and add it to the dictionary.
                    #if sum_dict != "":
                    if sum_dict is not None:
                        for row in sum_dict:
                            value = row[0].replace("\n", "")
                            expected_value = value.split('/')[-1]
                            if expected_value == endpointName.split('/')[-1]:
                                if method_name == row[1].lower():
                                    summary = row[-1]
                                    if summary[-1] == ".":
                                        dict_temp[endpointName][method_name][
                                            "summary"
                                        ] = summary
                                    else:
                                        dict_temp[endpointName][method_name][
                                            "summary"
                                        ] = (summary + ".")
                    # Add the description to the temp dictionary
                    dict_temp[endpointName][method_name]["description"] = description
                    # Set the operationId for the endpoint and method
                    endpoint_parts = endpointName.replace("_", "").split("/")

                    # Construct the operationId based on endpoint components
                    operation_id = ""
                    for part in endpoint_parts:
                        if "{" in part:
                            operation_id += part.split("{")[0].title()
                        else:
                            operation_id += part.title()

                    # Append the HTTP method name to the operationId
                    operation_id += method_name.upper()

                    # Check for path parameters and append them if they exist
                    if "{" in endpointName:
                        path_params = [param.split("}")[0] for param in endpointName.split("{")[1:]]
                        for param in path_params:
                            operation_id += param.title()

                    dict_temp[endpointName][method_name]["operationId"] = operation_id
                    # Set the tags for supported endpoint's methods
                    dict_temp[endpointName][method_name]["tags"] = []
                    bool = False
                    for tag in config["tags"]:
                        if endpointName.__contains__(tag):
                            dict_temp[endpointName][method_name]["tags"].append(tag)
                            bool = True
                    if bool == False:
                        dict_temp[endpointName][method_name]["tags"].append(
                            config["tags"][0]
                        )

            # passing the table to is_query_param_def_table, if the first row is according to the given conditions
            if isinstance(tmp_elem, Table) and is_query_param_def_table(tmp_elem):
                bool_to_make_dict_empty = True
                ndm = GenerateOAS(" ")
                # Parse the current query parameter definition table and get a dictionary of query parameters
                mydict = ndm.parse_query_param_table_elem(
                    tmp_elem, bool_to_make_dict_empty
                )
                definitions_count = definitions_count + 1
                # Loop through the new query parameters and compare them with the existing ones
                for key1 in mydict:
                    for key2 in all_quer_par_dict:
                        # Check if the description and cardinality match
                        if (
                            mydict[key1]["description"]
                            == all_quer_par_dict[key2]["description"]
                        ):
                            if (
                                mydict[key1]["cardinality"]
                                == all_quer_par_dict[key2]["cardinality"]
                            ):
                                # Add a reference to the existing parameter to the 'parameters' list of the endpoint and method
                                dict_temp.setdefault(endpointName, {}).setdefault(
                                    method_name, {}
                                ).setdefault("parameters", [])
                                dict_temp[endpointName][method_name][
                                    "parameters"
                                ].append(
                                    {
                                        "$ref": "#/components/parameters/"
                                        + key2.split(" ").pop(0)
                                    }
                                )

            # Check if tmp_elem is an instance of request or response table
            if isinstance(tmp_elem, Table) and is_api_def_table(tmp_elem):
                # Instantiate a GenerateOAS object
                ndm = GenerateOAS(" ")
                path_dict = ndm.parse_api_table_elem(tmp_elem)
                # Update the schemas dictionary with the new or updated parameters
                schemas_dict["paths"].update(dict_temp)
                # If there is a request body exists, add it to the schema
                if len(path_dict[1]) > 0 and method_name not in {"get", "delete"}:
                    schemas_dict["paths"][endpointName][method_name][
                        "requestBody"
                    ] = path_dict[1]
                # Add the responses defined in the path_dict to the schema
                schemas_dict["paths"][endpointName][method_name][
                    "responses"
                ] = path_dict[0]
    
                if "4xx" in path_dict[0]:
                    del path_dict[0]["4xx"]
                    schemas_dict["paths"][endpointName][method_name][
                        "responses"
                    ] = path_dict[0]
                    schemas_dict["paths"][endpointName][method_name]["responses"][
                        "401"
                    ] = {"$ref": "#/components/responses/401"}
                    schemas_dict["paths"][endpointName][method_name]["responses"][
                        "403"
                    ] = {"$ref": "#/components/responses/403"}
                    schemas_dict["paths"][endpointName][method_name]["responses"][
                        "404"
                    ] = {"$ref": "#/components/responses/404"}
                    schemas_dict["paths"][endpointName][method_name]["responses"][
                        "406"
                    ] = {"$ref": "#/components/responses/406"}
                    schemas_dict["paths"][endpointName][method_name]["responses"][
                        "416"
                    ] = {"$ref": "#/components/responses/416"}
                    schemas_dict["paths"][endpointName][method_name]["responses"][
                        "429"
                    ] = {"$ref": "#/components/responses/429"}
                if method_name == "delete":
                    noContent = {"204": {"$ref": "#/components/responses/204"}}
                    schemas_dict["paths"][endpointName][method_name][
                        "responses"
                    ].update(noContent)

                definitions_count = definitions_count + 1

                # It goes to the subscription endpoint POST table
                if "/subscriptions" in endpointName and method_name == "post":
                    first_cell = tmp_elem.rows[1].cells[1].text
                    # Checks for the first cell content
                    if "{NotificationSubscription}" in first_cell or "{" in first_cell:
                        # Checks for the last cell content
                        last_cell = tmp_elem.rows[1].cells[-1]
                        # Splits the content on the basis of the new line and add it into the list and also replaces '*'
                        lst = last_cell.text.replace("\u2022\t", "").split("\n")
                        # Removes the '.' at the end of the index value
                        for i, val in enumerate(lst):
                            if val[-1] == ".":
                                lst[i] = val[:-1]
                        # If there is one Subscription type an dthat is mentioned in the last cell not the first cell
                        if len(lst) == 2 and len(lst[1]) > 13:
                            multiple_remarks = False
                        else:
                            multiple_remarks = True
                        dict_temp[endpointName][method_name]["callbacks"] = {}
                        callbacks = dict_temp[endpointName][method_name]["callbacks"]
                        populate_callbacks(callbacks, multiple_remarks, lst)
                    else:
                        first_cell = first_cell.replace(" ", "").replace("\n", "")
                        lst = [first_cell]
                        dict_temp[endpointName][method_name]["callbacks"] = {}
                        callbacks = dict_temp[endpointName][method_name]["callbacks"]
                        populate_callbacks(callbacks, False, lst)
                
                if sec_endpoint:
                    schemas_dict["paths"][sec_endpoint] = deepcopy(schemas_dict["paths"][endpointName])

        else:
            # If tmp_elem is not a definition table, log an error and exit the loop
            logging.debug(
                "idx >=len(content): A=%s, B: %s, IDX: %s, len(content): %s",
                a_id,
                b_id,
                idx,
                len(content),
            )
            break

    return definitions_count


def is_query_param_def_table(table):
    """
    Determine if a table represents query parameters.

    This function checks whether a given table represents query parameters based on the column headers. A table is considered to represent query parameters if it contains columns with headers such as "Attribute name," "Data type," "Cardinality," and "Description." There are also variations in column headers that are considered valid.

    Args:
        table (Table): The table to check for query parameter representation.

    Returns:
        bool: True if the table represents query parameters, False otherwise.

    Notes:
        - The function checks if the table columns and headers match the expected patterns for query parameter tables.
        - Valid variations in column headers are considered.

    Example:
        This function can be used to identify and filter out tables in a document that represent query parameters. It's particularly useful for automated extraction of query parameter definitions from documents.

    See Also:
        - `generate_api_def_tables_between` function for extracting API definitions, including query parameters, from a document.
    """

    expected_labels = ["Name", "Data type", "Cardinality", "Remarks"]
    expected_labels_v2 = ["Name", "Data type", "Cardinality", "Description"]
    expected_labels_v3 = ["Name", "Cardinality", "Remarks"]
    expected_labels_v4 = ["Attribute name", "Cardinality", "Description"]
    expected_labels_v5 = ["Name", "Cardinality", "Description"]
    expected_labels_v6 = ["Attribute name", "Data type", "Cardinality", "Description"]

    labels = [table.columns[i].cells[0].text.strip().replace("\n", " ") for i in range(len(table.columns))]

    if labels == expected_labels:
        logging.debug("Query Parameter Table found (Name, Data type, Cardinality, Remarks).")
    if labels == expected_labels_v2:
        logging.debug("Query Parameter Table found (Name, Data type, Cardinality, Description).")
    if labels == expected_labels_v3:
        logging.debug("Query Parameter Table found (Name, Cardinality, Remarks).")
    if labels == expected_labels_v4:
        logging.debug("Query Parameter Table found (Attribute name, Cardinality, Description).")
    if labels == expected_labels_v5:
        logging.debug("Query Parameter Table found (Name Cardinality, Description).")
    if labels == expected_labels_v6:
        logging.debug("Query Parameter Table found (Attribute name, Data type, Cardinality, Description).")

    return (
        (len(table.columns) == 4 and labels == expected_labels)
        or (len(table.columns) == 4 and labels == expected_labels_v2)
        or (len(table.columns) == 3 and labels == expected_labels_v3)
        or (len(table.columns) == 3 and labels == expected_labels_v4)
        or (len(table.columns) == 3 and labels == expected_labels_v5)
        or (len(table.columns) == 4 and labels == expected_labels_v6)
    )


def is_api_def_overview_table(table):
    """
    Determine if a table represents an API definition overview.

    This function checks whether a given table represents an API definition overview based on the column headers. An API definition overview typically contains information about resource names, URIs, HTTP methods, and their meanings.

    Args:
        table (Table): The table to check for API definition overview representation.

    Returns:
        bool: True if the table represents an API definition overview, False otherwise.

    Notes:
        - The function checks if the table columns and headers match the expected patterns for API definition overviews.
        - Valid variations in column headers are considered.

    Example:
        This function can be used to identify and filter out tables in a document that represent API definition overviews. It's particularly useful for automated extraction of API definitions from documents.

    See Also:
        - `generate_api_def_tables_between` function for extracting API definitions from a document.
    """
    expected_labels = ["Resource name", "Resource URI", "HTTP method", "Meaning"]
    expected_labels_v2 = ["Resource name", "Resource URI", "HTTP Method", "Description"]
    # Workaround needed for NFV tables
    expected_labels_nfv = ["Resource name", "Resource URI", "HTTP Method", "Cat", "Meaning"]

    labels = [table.columns[i].cells[0].text.strip().replace("\n", " ") for i in range(len(table.columns))]

    if labels == expected_labels:
        logging.debug("API Definition main table found (Resource name, Resource URI, HTTP method, Meaning.")
    if labels == expected_labels_v2:
        logging.debug("API Definition main table found (Resource name, Resource URI, HTTP method, Description.")
    if labels == expected_labels_nfv:
        logging.debug("API Definition main table found (Resource name, Resource URI, HTTP Method, Cat, Meaning).")

    return (
           (len(table.columns) == 4 and labels == expected_labels)
           or (len(table.columns) == 4 and labels == expected_labels_v2)
           or (len(table.columns) == 5 and labels == expected_labels_nfv)
    )


def is_api_def_table(table):
    """
    Determine if a table represents an API data model.

    This function checks whether a given table represents an API data model based on the column headers. An API data model table typically contains information about request or response bodies, including attributes' names, data types, cardinalities, and descriptions.

    Args:
        table (Table): The table to check for API data model representation.

    Returns:
        bool: True if the table represents an API data model, False otherwise.

    Notes:
        - The function checks if the table columns and headers match the expected patterns for API data model tables.
        - Valid variations in column headers are considered.

    Example:
        This function can be used to identify and filter out tables in a document that represent API data models. It's particularly useful for automated extraction of API data models from documents.

    See Also:
        - `generate_api_def_tables_between` function for extracting API data models from a document.
    """

    expected_labels = ["Request body", "Data type", "Cardinality", "Remarks", "Remarks"]

    expected_labels_v2 = [
        "Request message content",
        "Data type",
        "Cardinality",
        "Remarks",
        "Remarks",
    ]

    expected_labels_v3 = [
        "Response body",
        "Data type",
        "Cardinality",
        "Response codes",
        "Remarks",
    ]

    expected_labels_v1 = [
        "Response body",
        "Data type",
        "Cardinality",
        "Response Codes",
        "Remarks"
    ]


    expected_labels_v4 = [
        "Response message content",
        "Data type",
        "Cardinality",
        "Response codes",
        "Remarks",
    ]

    expected_labels_nfv = ["Request body", "Data type", "Cardinality", "Description", "Description"]
    expected_labels_nfv_v1 = ["Response body", "Data type", "Cardinality", "Response codes", "Description"]

    labels = [table.columns[i].cells[0].text.strip() for i in range(len(table.columns))]

    if labels == expected_labels:
        logging.debug("API Definition request Table found (Request body, Data type, Cardinality, Remarks, Remarks).")
    if labels == expected_labels_v1:
        logging.debug("API Definition request Table found (Response body, Data type, Cardinality, Response Codes, Remarks.")
    if labels == expected_labels_v2:
        logging.debug("API Definition response Table found (Request message content, Data type, Cardinality, Remarks, Remarks).")
    if labels == expected_labels_v3:
        logging.debug("API Definition response Table found (Response body, Data type, Cardinality, Response codes, Remarks).")
    if labels == expected_labels_v4:
        logging.debug("API Definition response Table found (Response message content, Data type, Cardinality, Response codes, Remarks).")
    if labels == expected_labels_nfv:
        logging.debug("API Definition request Table found (Request body, Data type, Cardinality, Description).")
    if labels == expected_labels_nfv_v1:
        logging.debug("API Definition response Table found (Response body, Data type, Cardinality, Response codes, Descripition).")

    return (
        (len(table.columns) == 5 and labels == expected_labels)
        or (len(table.columns) == 5 and labels == expected_labels_v1)
        or (len(table.columns) == 5 and labels == expected_labels_v2)
        or (len(table.columns) == 5 and labels == expected_labels_v3)
        or (len(table.columns) == 5 and labels == expected_labels_v4)
        or (len(table.columns) == 5 and labels == expected_labels_nfv)
        or (len(table.columns) == 5 and labels == expected_labels_nfv_v1)
    )

# Parent class of GenerateOAS

class APIDefinition:
    """
    Represents an API Definition.

    This class is used for parsing and managing API definitions, specifically endpoints, and their associated data models.

    Args:
        elem (str or Element): Either a string representing the endpoint or an Element object representing a document element containing the endpoint.

    Attributes:
        endpoint (str): The raw endpoint string.
        endpoint_clean (str): A cleaned version of the endpoint.
        data_definition (dict): A dictionary containing data definitions associated with the endpoint.

    Methods:
        parse_query_param_table_elem(elem, bool_to_make_dict_empty, reverse_order=False):
            Parses a query parameter table element and returns the associated data definition dictionary.

        parse_api_table_elem(elem, reverse_order=False):
            Parses an API table element and returns the associated data definition dictionary.
    """
    # Define an __init__ method that initializes an instance of the class
    def __init__(self, elem):
        """
        Initialize an instance of the APIDefinition class.

        Args:
            elem (str or Element): Either a string representing the endpoint or an Element object representing a document element containing the endpoint.
        """
        # If the input is a string, set the endpoint and clean endpoint attributes to the input string
        if isinstance(elem, str):
            self.endpoint = elem
            self.endpoint_clean = elem
        # If the input is not a string, extract the endpoint from the input element and clean it
        else:
            self.endpoint = elem.text
            endpoints = ["v2/", "v1/", "v3/"]
            for ep in endpoints:
                if ep in self.endpoint:
                    clean_endpoint = self.endpoint[
                        self.endpoint.index(ep) + 2 :
                    ].replace(" ", "")
                    if clean_endpoint[-1] == "/" or clean_endpoint[-1] == ".":
                        self.endpoint_clean = clean_endpoint[:-1]
                    else:
                        self.endpoint_clean = clean_endpoint
                    break
            else:
                self.endpoint_clean = self.endpoint

        logging.debug("-- Endpoint: " + self.endpoint_clean)
        # Initialize an empty data definition attribute
        self.data_definition = {}

    # Define a method called parse_query_param_table_elem that parses a query parameter table element
    def parse_query_param_table_elem(
        self, elem, bool_to_make_dict_empty, reverse_order=False
    ):
        """
        Parse a query parameter table element and return the associated data definition.

        This method takes a table element representing query parameters, converts it to a string matrix,
        and then extracts and parses the data definition from it.

        Args:
            elem (Element): The table element to parse.
            bool_to_make_dict_empty (bool): A flag to indicate whether to empty the data definition dictionary.
            reverse_order (bool, optional): A flag to indicate whether to reverse the order of elements in the table. Default is False.

        Returns:
            dict: A dictionary containing the parsed data definition for query parameters.

        Example:
            >>> elem = <table element representing query parameters>
            >>> bool_to_make_dict_empty = True
            >>> reverse_order = False
            >>> data_definition = parse_query_param_table_elem(elem, bool_to_make_dict_empty, reverse_order)
        """
        # Convert the table element to a string matrix and extract the data definition
        string_matrix = docx_tab_to_string_matrix_for_query_param_def(
            elem, reverse_order
        )[1:]
        self.data_definition = self.parse_query_param_data_definition(
            string_matrix, bool_to_make_dict_empty
        )
        return self.data_definition

    # Define a method called parse_api_table_elem that parses an API table element
    def parse_api_table_elem(self, elem, reverse_order=False):
        """
        Parse an API table element and return the associated data definition.

        This method takes a table element representing an API data model, converts it to a string matrix,
        and then extracts and parses the data definition from it.

        Args:
            elem (Element): The table element to parse.
            reverse_order (bool, optional): A flag to indicate whether to reverse the order of elements in the table. Default is False.

        Returns:
            dict: A dictionary containing the parsed data definition for the API data model.

        Example:
            >>> elem = <table element representing an API data model>
            >>> reverse_order = False
            >>> data_definition = parse_api_table_elem(elem, reverse_order)
        """
        # Convert the table element to a string matrix and extract the data definition
        string_matrix = docx_tab_to_string_matrix_for_api_def(elem, reverse_order)[1:]
        self.data_definition = self.parse_api_data_definition(string_matrix)
        return self.data_definition


# Define a class called GenerateOAS that inherits from the APIDefinition class
class GenerateOAS(APIDefinition):
    """
    A class for generating OpenAPI Specifications (OAS) from API definition elements.

    This class inherits from the APIDefinition class and provides methods for parsing query parameter
    and API data definition tables and converting them into an OAS-compatible format.

    Args:
        elem (str or Element): The input element, either as a string or an Element object, containing
            API definition information.

    Attributes:
        endpoint (str): The endpoint extracted from the input element.
        endpoint_clean (str): The cleaned endpoint extracted from the input element.
        data_definition (dict): A dictionary containing the parsed data definition.

    Methods:
        parse_query_param_data_definition(string_matrix, bool_to_make_dict_empty):
            Parses a query parameter data definition and returns an OAS-compatible dictionary.

        parse_api_data_definition(string_matrix):
            Parses an API data definition and returns an OAS-compatible dictionary.

    Example:
        >>> elem = "API definition element content"
        >>> generator = GenerateOAS(elem)
        >>> query_param_data = generator.parse_query_param_data_definition(string_matrix, True)
    """
    # Define an __init__ method that calls the parent class's __init__ method
    def __init__(self, elem):
        """
        Initialize a GenerateOAS object.

        Args:
            elem (str or Element): The input element, either as a string or an Element object,
                containing API definition information.

        Example:
            >>> elem = "API definition element content"
            >>> generator = GenerateOAS(elem)
        """
        APIDefinition.__init__(self, elem)

    # Define a method called parse_query_param_data_definition that parses a query parameter data definition
    def parse_query_param_data_definition(self, string_matrix, bool_to_make_dict_empty):
        """
        Parse a query parameter data definition from a string matrix and return an OAS compatible dictionary.

        Args:
            string_matrix (List[List[str]]): A 2D list representing the query parameter data definition table.
            bool_to_make_dict_empty (bool): A boolean indicating whether to empty the dictionary before adding new entries.

        Returns:
            dict: An OAS compatible dictionary representing the query parameters.

        Example:
            >>> matrix = [
            ...     ["Name", "Data type", "Cardinality", "Description"],
            ...     ["param1", "string", "optional", "This is parameter 1"],
            ...     ["param2", "integer", "required", "This is parameter 2"]
            ... ]
            >>> generator = GenerateOAS("API element")
            >>> query_params = generator.parse_query_param_data_definition(matrix, True)
        """
        # get_oas_data_definition_obj takes string_matrix as input and return an OAS compatible dictionary for query parameters
        return get_oas_for_query_param_data_definition(
            string_matrix, bool_to_make_dict_empty
        )

    # Define a method called parse_api_data_definition that parses an API data definition
    def parse_api_data_definition(self, string_matrix):
        """
        Parse an API data definition from a string matrix and return an OAS compatible dictionary.

        Args:
            string_matrix (List[List[str]]): A 2D list representing the API data definition table.

        Returns:
            dict: An OAS compatible dictionary representing the API data definition.

        Example:
            >>> matrix = [
            ...     ["Attribute name", "Data type", "Cardinality", "Description"],
            ...     ["attribute1", "string", "optional", "This is attribute 1"],
            ...     ["attribute2", "integer", "required", "This is attribute 2"]
            ... ]
            >>> generator = GenerateOAS("API element")
            >>> api_data = generator.parse_api_data_definition(matrix)
        """
        global config
        # get_oas_data_definition_obj takes string_matrix as input and return an OAS compatible dictionary for api tables
        return get_oas_for_api_data_definition(string_matrix, config)

def maindoc2oas(filename, configfile):
    global OAS_DICT
    global config
    global MODELS

    logging.basicConfig(level=logging.DEBUG)
    
    with open(configfile, encoding="utf8") as file:
        logging.info("Opening configuration file: %s", configfile)
        config = yaml.safe_load(file)
    
    API_SPEC_FN = filename

    MODELS = {"oas": oas_output_info(API_SPEC_FN[:-5], "")}

    for fdt in range(FAKE_DATA_TYPES_COUNT):
        if config["fake_data_types"]:
            logging.debug("Start reading fake data types...")
            add_fake_datatype(OAS_DICT, fdt)

    if hasattr(config, "manual_types") or "manual_types" in config:
        logging.debug("Start reading manual types...")
        for attr in config["manual_types"]:
            print("MANUAL TYPE ADDED:", attr, config["manual_types"][attr])
            # the add_manual_datatype function takes the manual_types defined in the config file and stores them in the OAS_DICT variable under 'components': 'schemas'
            add_manual_datatype(OAS_DICT, attr, config["manual_types"][attr])

    if "info" in config:
        logging.debug("Start reading info...")
        OAS_DICT["info"] = config["info"]
    if "servers" in config:
        logging.debug("Start reading servers...")
        OAS_DICT["servers"] = config["servers"]
    # in iterative manner each heading element from config['data_model_headings'] will be passed to generate_oas function
    for heading in config["data_model_headings"]:
        logging.debug("Start converting data model headings...")
        if heading:
            DATA_MODELS_HEADINGS = config["data_model_headings"][heading]
        # the core function which translates complete Data Model tables and appends them to the OAS_DICT variable
        generate_oas(API_SPEC_FN, DATA_MODELS_HEADINGS)

    # Populate referenced Data models under Schemas components
    OAS_DICT["components"]["schemas"].update(DICT_FOR_REF_DM)
    OAS_DICT["components"]["responses"].update(config["responses"])

    for heading in config["api_def_headings"]:
        logging.debug("Start converting api def headings...")
        if heading:
            API_DEF_HEADING = config["api_def_headings"][heading]

        generate_API_def_oas(API_SPEC_FN, API_DEF_HEADING)

    update_key_value_pair_entries()  ##It updates the KeyValuePair(s) entry in the OAS

    while (
        replace_str_to_object_values() != -1
    ):  ##It updates the map(<data_model_name>) entry in the OAS
        OAS_DICT = json.loads(replace_str_to_object_values())
    add_new_str_to_obj_data_value()

    add_parameters_to_endpoints_print_all_files(OAS_DICT)

    #Reset global variables
    MODELS = {}
    OAS_DICT = {}
    config = {}
    new_data_models = set()
    sum_dict = None

    OAS_DICT["openapi"] = "3.1.0"
    OAS_DICT["jsonSchemaDialect"] = "https://json-schema.org/draft/2020-12/schema"
    OAS_DICT["info"] = {}
    OAS_DICT["servers"] = {}
    OAS_DICT["paths"] = {}
    OAS_DICT["components"] = {"schemas": {}}
    OAS_DICT["components"]["responses"] = {}
    OAS_DICT["components"]["parameters"] = {}
#################################################################################

if __name__ == "__main__":
    """
    Main script for generating OpenAPI Specifications (OAS) from a DOCX file.

    This script reads configuration settings from a YAML file and processes the DOCX file containing
    API definitions. It generates OAS definitions for data models and API endpoints and outputs the
    resulting OAS to a file.

    Example:
        $ python script.py input.docx config.yaml
    """
    logging.basicConfig(level=logging.DEBUG)

    with open(sys.argv[2], encoding="utf8") as file:
        logging.info("Opening configuration file: %s", sys.argv[2])
        config = yaml.safe_load(file)

    try:
        API_SPEC_FN = sys.argv[1]
    except:
        logging.critical("Error: Filename missing or filename not a docx document")
        logging.critical("Usage: doc2oas <docx-file> <config-file>")
        sys.exit(1)

    MODELS = {"oas": oas_output_info(API_SPEC_FN[:-5], "")}

    for fdt in range(FAKE_DATA_TYPES_COUNT):
        if config["fake_data_types"]:
            add_fake_datatype(OAS_DICT, fdt)

    print(config)

    if hasattr(config, "manual_types") or config["manual_types"]:
        for attr in config["manual_types"]:
            print("MANUAL TYPE ADDED:", attr, config["manual_types"][attr])
            # the add_manual_datatype function takes the manual_types defined in the config file and stores them in the OAS_DICT variable under 'components': 'schemas'
            add_manual_datatype(OAS_DICT, attr, config["manual_types"][attr])

    OAS_DICT["info"] = config["info"]
    OAS_DICT["servers"] = config["servers"]

    # in iterative manner each heading element from config['data_model_headings'] will be passed to generate_oas function
    for heading in config["data_model_headings"]:
        if heading:
            DATA_MODELS_HEADINGS = config["data_model_headings"][heading]
        # the core function which translates complete Data Model tables and appends them to the OAS_DICT variable
        generate_oas(API_SPEC_FN, DATA_MODELS_HEADINGS)

    # Populate referenced Data models under Schemas components
    OAS_DICT["components"]["schemas"].update(DICT_FOR_REF_DM)
    OAS_DICT["components"]["responses"].update(config["responses"])

    for heading in config["api_def_headings"]:
        if heading:
            API_DEF_HEADING = config["api_def_headings"][heading]

        generate_API_def_oas(API_SPEC_FN, API_DEF_HEADING)

    update_key_value_pair_entries()  ##It updates the KeyValuePair(s) entry in the OAS

    while (
        replace_str_to_object_values() != -1
    ):  ##It updates the map(<data_model_name>) entry in the OAS
        OAS_DICT = json.loads(replace_str_to_object_values())
    add_new_str_to_obj_data_value()

    # print_to_files()
    modified_oas_dict = add_parameters_to_endpoints_print_all_files(OAS_DICT)
