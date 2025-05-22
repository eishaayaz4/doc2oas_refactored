#!/bin/python3
"""
Model one data field
"""

import re
from ast import Pass
from utils import INLINED_TYPE
from utils import SPC
import sys
import yaml

BASIC_TYPES = [
    "array",
    "boolean",
    "integer",
    "number",
    "object",
    "string",
    "integer (0..100)",
    "enum (inlined)",
    "anyuri",
    "uri",
    "array (uri)",
]
VALID_CODES = [
    "200",
    "201",
    "204",
    "206",
    "400",
    "401",
    "403",
    "404",
    "406",
    "412",
    "414",
    "416",
    "415",
    "422",
    "429",
    "4xx",
    "5xx",
]


class Rule:
    """
    Rule class to model policies on data fields.

    Attributes:
        condition (tuple): A tuple containing the condition details.
        settings (list): A list of settings for the rule.

    Methods:
        pre_name(self):
            Getter for the first condition.
        
        pre_value(self):
            Getter for the second condition.
    """

    def __init__(self, condition, settings):
        """
        Initialize a Rule instance.

        Args:
            condition (tuple): A tuple containing the condition details.
            settings (list): A list of settings for the rule.
        """
        self.condition = condition
        self.settings = settings

    def pre_name(self):
        """
        Getter for the first condition.

        Returns:
            str: The first condition.
        """
        return self.condition[0]

    def pre_value(self):
        """
        Getter for the second condition.

        Returns:
            str: The second condition.
        """
        return self.condition[1]


DEFAULT_RULES = [
    Rule(
        ("literal_type", "String"),
        [("clean_type", "string"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "Float"),
        [("clean_type", "number"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "Boolean"),
        [("clean_type", "boolean"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "Bool"),
        [("clean_type", "bool"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "Integer"),
        [("clean_type", "integer"), ("has_basic_type", "True")],
    ),
    Rule(("literal_type", "Enum (inlined)"), [("literal_type", "Enum_inlined")]),
    Rule(("literal_type", "Enum (inline)"), [("literal_type", "Enum_inline")]),
    Rule(
        ("literal_type", "Int"), [("clean_type", "integer"), ("has_basic_type", "True")]
    ),
    Rule(
        ("literal_type", "Object"),
        [("clean_type", "integer"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "KeyValuePairs"),
        [("clean_type", "object"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "KeyValuePair"),
        [("clean_type", "object"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "Structure (inlined)"),
        [("clean_type", "object"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "Structure (inline)"),
        [("clean_type", "object"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "array(Structure (inlined))"),
        [("clean_type", "array"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "Not specified"),
        [
            ("clean_type", "object"),
            ("has_basic_type", "True"),
            ("literal_type", "Not_specified"),
        ],
    ),
    Rule(
        ("literal_type", "Not Specified"),
        [
            ("clean_type", "object"),
            ("has_basic_type", "True"),
            ("literal_type", "Not_specified"),
        ],
    ),
    # Todo add min and max values for integer below
    Rule(
        ("literal_type", "Integer (0..100)"),
        [("clean_type", "integer"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "Uint8"),
        [("clean_type", "integer"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "UnsignedInt"),
        [("clean_type", "integer"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "Float"),
        [("clean_type", "number"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "Array(Structure (inlined))"),
        [("clean_type", "array"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "array(Structure inlined)"),
        [("clean_type", "array"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "array(Structure (inline))"),
        [("clean_type", "array"), ("has_basic_type", "True")],
    ),
    Rule(
        ("literal_type", "Structure"),
        [("clean_type", "object"), ("has_basic_type", "True")],
    ),
]


class DataField:
    """
    Defines a data field for a data type definition in the OAS.

    Attributes:
        name (str): The name of the data field.
        literal_type (str): The literal type of the data field.
        cardinality (str): The cardinality of the data field.
        description (str): The description of the data field.
        extras (list): A list of extra information for the data field.

    Methods:
        __init__(self, name="", literal_type="", cardinality="", description=""):
            Initializes a DataField instance.
        
        to_dict(self):
            Exports the content of the data field as a dictionary.
    """

    def __init__(self, name="", literal_type="", cardinality="", description=""):
        """
        Initializes a DataField instance.

        Args:
            name (str): The name of the data field.
            literal_type (str): The literal type of the data field.
            cardinality (str): The cardinality of the data field.
            description (str): The description of the data field.
        """

        self.name = name.replace(">", "").strip()
        if "Array(" in literal_type or "Array (" in literal_type or "array(" in literal_type:
            m = re.search(r"\((.*?)\)", literal_type)
            if m:
                self.literal_type = m.group(1)
        else:
            self.literal_type = literal_type.strip().split(" (0..")[0].split("OR")[0]
        self.cardinality = cardinality
        self.description = description
        if self.literal_type == 'Enum (inlined':
            self.literal_type = literal_type
        self.extras = []
        if self.literal_type == "Bool":
            self.literal_type = "boolean"
        self.is_note = self.name.startswith("NOTE") or self.name.startswith("Note")

        if self.is_note:
            self.is_required = False
            self.is_array = False
            return None

        self.has_inlined = (INLINED_TYPE in self.literal_type) and not self.is_note

        if self.literal_type == "0..N":
            self.literal_type = self.cardinality
            self.cardinality = "0..N"

        self.is_required = not self.is_note and not "0" in self.cardinality

        if self.has_inlined or self.literal_type == '1':
            self.clean_type = "object"
        else:
            self.clean_type = self.literal_type

        self.has_basic_type = self.clean_type in BASIC_TYPES

        if "uint" in self.literal_type.lower():
            self.clean_type = "integer"
            self.has_basic_type = True
            self.extras.append(("format", self.literal_type.lower()))

        if "uint32" in self.literal_type.lower():
            self.clean_type = "integer"
            self.has_basic_type = True
            self.extras.append(("format", self.literal_type.lower()))

        if "float" in self.literal_type.lower():
            self.clean_type = "number"
            self.has_basic_type = True
            self.extras.append(("format", "float"))

        if self.literal_type.strip() in ["AnyURI", "URI", "Uri"]:
            self.clean_type = "string"
            self.has_basic_type = True
            self.extras.append(("format", "uri"))

        if self.name.strip() == "(inherited attributes)":
            self.clean_type = "object"
            self.has_basic_type = True
            self.name = "inherited_attributes"
            self.cardinality = "1"
            self.literal_type = "inherited_attributes"

        self.is_enum = "Enum" in self.literal_type

        for rule in DEFAULT_RULES:
            if getattr(self, rule.pre_name()) == rule.pre_value():
                for setting in rule.settings:
                    if setting[1] == "True" or setting[1] == "False":
                        setattr(self, setting[0], True)
                    elif setting[1] == "False":
                        setattr(self, setting[0], False)
                    else:
                        setattr(self, setting[0], setting[1])

        self.is_enum_inlined = ("Enum_inlined" in self.literal_type) or (
            "Enum_inline" in self.literal_type
        )
        if self.literal_type == "Float" and self.cardinality == "1..N":
            isLikelyAnArray = False
        else:
            isLikelyAnArray = False
            for char in self.cardinality:
                if char.isalpha():
                    isLikelyAnArray = True

        if isLikelyAnArray and not self.is_note and self.literal_type != "array(Enum (inlined))":
            self.clean_type = "array"
            self.is_array = True
            self.has_basic_type = True
            if self.cardinality.strip()[0].isdigit():
                self.extras.append(("minItems", int(self.cardinality.strip()[0])))
            if self.has_inlined and not self.is_enum:
                Pass
            elif self.literal_type == "String":
                self.extras.append(("items", {"type": "string"}))
            elif self.literal_type == "Integer":
                self.extras.append(("items", {"type": "integer"}))
            elif (self.literal_type == "Enum") or (self.literal_type == "Enum_inlined"):
                if (
                    ("0 =" in self.description)
                    or ("1 =" in self.description)
                    or ("Numeric value" in self.description)
                    or ("numeric value" in self.description)
                ):
                    self.extras.append(("items", {"type": "integer"}))
                else:
                    self.extras.append(("items", {"type": "string"}))
            elif self.literal_type == "Float":
                self.extras.append(("items", {"type": "float"}))
            elif self.literal_type == "1" and self.cardinality == "Structure (inlined)":
                self.extras.append(
                    ("items", {"$ref": "#/components/schemas/" + self.name})
                )
            elif self.literal_type == "1" and self.cardinality == "LinkType":
                self.extras.append(
                    ("items", {"$ref": "#/components/schemas/" + self.cardinality})
                )
            elif self.literal_type != '1':
                self.extras.append(
                    ("items", {"$ref": "#/components/schemas/" + self.literal_type})
                )
        else:
            self.is_array = False

    def to_dict(self):
        """
        Exports the content of the data field as a dictionary.

        Returns:
            dict: A dictionary representation of the data field.
        """
        res = {}

        if self.is_note:
            return self.name

        if self.has_basic_type:
            res["description"] = self.description
            if self.is_array and self.has_inlined:
                res["type"] = "object"
            else:
                res["type"] = self.clean_type         
        else:
            if self.is_enum or self.is_enum_inlined:
                if (
                    ("0 =" in self.description)
                    or ("1 =" in self.description)
                    or ("Numeric value" in self.description)
                    or ("numeric value" in self.description)
                ):
                    res["type"] = "integer"
                else:
                    res["type"] = "string"
                res["description"] = self.description
                if re.findall(r"\b\d+\s*=\s*", self.description):
                    numbers = re.findall(r"\b\d+\s*=\s*", self.description)
                    if (self.cardinality[-1] == "1" ):
                        res["enum"] = [int(s.strip("= \t")) for s in numbers]
                    elif (self.cardinality[-1] > "1" ):
                        res['minItems'] = int(self.cardinality[:1])
                        res['maxItems'] = int(self.cardinality[-1])
                        res["type"] = "array" 
                        res["items"] = {
                                    "enum": [int(s.strip("= \t")) for s in numbers],
                                    "type": "integer" }
                else:
                    res["enum"] = ["SEE_DESCRIPTION"]
            elif self.literal_type == "Not specified":
                res["description"] = self.description
                res["type"] = "string"
            else:
                self.description = " ".join(self.description.split())
                res["description"] = self.description
                # Get only the first word in clean_type to be displayed in $ref
                res["$ref"] = "#/components/schemas/" + self.clean_type.strip().split(
                    " "
                ).pop(0)
                res["type"] = "object"

        for key, val in self.extras:
            # Skip minItems if type is object
            if key == "minItems" and res.get("type") == "object":
                continue
            res[key] = val

        return res


########### Functions related to API Definitions implementation #################
#################################################################################
class QueryTableRow:
    """
    Defines a data field for a data type definition in the OAS.

    Attributes:
        name (str): The name of the query parameter.
        data_type (str): The data type of the query parameter.
        cardinality (str): The cardinality of the query parameter.
        summary (str): The summary description of the query parameter.
        is_note (bool): True if the query parameter is a note, False otherwise.
        is_required (bool): True if the query parameter is required, False otherwise.

    Methods:
        __init__(self, name="", data_type="", cardinality="", summary=""):
            Initializes a QueryTableRow instance.
        
        to_dict_for_query_param_def(self):
            Converts the QueryTableRow instance to a dictionary for query parameter definition.
    """

    def __init__(self, name="", data_type="", cardinality="", summary=""):
        """
        Initializes a QueryTableRow instance.

        Args:
            name (str): The name of the query parameter.
            data_type (str): The data type of the query parameter.
            cardinality (str): The cardinality of the query parameter.
            summary (str): The summary description of the query parameter.
        """

        # to handle cases when query param table has 3 columns and data type is not given
        if summary == "":
            summary = cardinality
        if (
            data_type[:5] == "0"
            or data_type[:5] == "1"
            or data_type[:5].__contains__("..") == True
        ):
            cardinality = data_type
            data_type = ""

        clean_name = name.strip().replace("\n", "")
        clean_name = clean_name.strip().replace(" ", "")
        self.name = "Query." + clean_name.capitalize()
        self.data_type = data_type.lower().strip().split(' ')[0]
        self.cardinality = cardinality
        self.clean_type = data_type

        if summary == "":
            self.summary = summary
        else:
            if summary[-1] == ".":
                self.summary = summary
            else:
                self.summary = summary + "."

        self.is_note = self.name[6:].startswith("NOTE") or self.name[6:].startswith(
            "Note"
        )

        self.is_required = not self.is_note and not "0" in self.cardinality

    def to_dict_for_query_param_def(self):
        """
        Converts the QueryTableRow instance to a dictionary that conforms to the OpenAPI Specification (OAS)
        for defining a query parameter.

        This method creates a dictionary representation of the query parameter, including its description, name,
        cardinality, data type, and other properties required for query parameter definition in OAS.

        Returns:
            dict: A dictionary conforming to the OAS specification, representing the query parameter
                for query parameter definition.

        Notes:
            - If the query parameter is marked as a 'note,' it will be excluded from the result.
            - Tables with no query parameters are excluded from the result.
        """

        res = {}
        schema = {}

        # excludes note if exist in table
        if self.is_note:
            print("ignore note")
        
        if self.data_type.__contains__("array("):
            self.data_type = self.data_type.replace("array(", "")
            self.data_type = self.data_type.replace(")", "")
        
        # excludes tables with no query parameters
        if self.name[6:].replace("/", "").lower() == "na":
            print("Query Parameter Table does not exist")
        else:
            # Exports the content of the data field as a dictionary
            res[self.name] = {
                "description": self.summary,
                "name": self.name[6:].lower(),
                "cardinality": self.cardinality,
                "in": "query",
                "required": self.is_required,
                "x-exportParamName": self.name,
                "schema": {
                    "type": "string"
                }
            }

            # checks whether cardinality is an array
            isLikelyAnArray = False
            for char in self.cardinality:
                if char.isalpha():
                    isLikelyAnArray = True

            # checks data type to append values in schema
            if self.data_type != "":
                if self.data_type in ["int32", "integer", "int", "uint32", "enum"]:
                    self.data_type = "integer"
                if self.data_type in ["anyuri", "uri", "array (uri)"]:
                    self.data_type = "string"
                if self.cardinality == '1..2' and self.data_type == "array":
                    self.data_type = "string"
                if self.data_type.lower() in BASIC_TYPES:
                    if isLikelyAnArray or self.cardinality == '1..2':
                        schema[self.name] = {
                            "type": "array",
                            "items": {"type": self.data_type},
                        }
                    else:
                        schema[self.name] = {"type": self.data_type}
                    res[self.name]["schema"] = schema[self.name]
                else:
                    schema[self.name] = {
                        "$ref": "#/components/schemas/"
                        + self.clean_type.strip().split(" ").pop(0)
                    }
                    res[self.name]["schema"] = schema[self.name]

                if self.data_type == "float":
                    schema[self.name] = {"format": self.data_type, "type": "number"}
                    res[self.name]["schema"] = schema[self.name]

            return res


class ApiTableRow:
    """
    Defines an API response or request based on a data type definition in the OAS.

    Attributes:
        data_type (str): The data type of the API response or request.
        cardinality (str): The cardinality of the API response or request.
        response_code (str): The response code for an API response.
        description (str): The description of the API response or request.
        is_required (bool): True if the API response or request is required, False otherwise.

    Methods:
        __init__(self, data_type="", cardinality="", response_code="", description=""):
            Initializes an ApiTableRow instance.
        
        to_dict_for_api_def(self):
            Converts the ApiTableRow instance to a dictionary for API definition.
    """
    # Initializes an instance of ApiTableRow with the provided data_type, cardinality, response_code, and description.
    def __init__(self, data_type="", cardinality="", response_code="", description=""):
        """
        Initializes an ApiTableRow instance.

        Args:
            data_type (str): The data type of the API response or request.
            cardinality (str): The cardinality of the API response or request.
            response_code (str): The response code for an API response.
            description (str): The description of the API response or request.
        """
        # Cleans up the inputs and sets instance variables accordingly.
        self.data_type = data_type.strip().replace(" ", "").replace("\n", '')
        self.cardinality = cardinality
        self.response_code = response_code[:3].replace(" ", "")
        self.description = description
        # Add a period at the end of the description if it doesn't already have one
        if description != "":
            if description[-1] == ".":
                self.description = description
            else:
                self.description = description + "."
        self.is_required = not "0" in self.cardinality

    def to_dict_for_api_def(self, config):
        """
        Converts an instance of ApiTableRow to a dictionary conforming to the OpenAPI Specification (OAS).

        This method creates two dictionaries: 'res' for API response information and 'request' for API request information.
        These dictionaries are formatted according to the OAS for defining API responses and requests.

        Returns:
            tuple: A tuple containing two dictionaries, 'res' and 'request', representing API response and request
                information, respectively.

        """
        res = {}
        request = {}
        
        # checks whether cardinality is an array
        isLikelyAnArray = False
        for char in self.cardinality:
            if char.isalpha():
                isLikelyAnArray = True

        if self.data_type.__contains__("array("):
            self.data_type = self.data_type.replace("array(", "")
            self.data_type = self.data_type.replace(")", "")
        
        if self.response_code == 206:
            res[self.response_code] = {
                                    "$ref": "#/components/responses/"
                                    + self.response_code
                                }
        if self.data_type == "n/a" and self.response_code in [
            "200",
            "201",
            "204",
            "202",
        ]:
            res[self.response_code] = {
                "description": self.description,
                "content": {
                    "application/json": {"schema": {"type": "object", "properties": {}}}
                },
            }
        else:
            if (
                self.data_type.replace("/", "").lower() != "na"
            ):
                if self.description != "":
                    if self.data_type != "Datatype":
                        # Check if the response_code is in the list of valid codes
                        if self.response_code in VALID_CODES:
                            # If the response_code is 200 or 201, add a dictionary to res with a schema
                            if self.response_code in ["200", "201"]:
                                if isLikelyAnArray:
                                    self.cardinality = "array"
                                    res[self.response_code] = {
                                        "description": self.description,
                                        "content": {
                                            "application/json": {
                                                "schema": {
                                                    "type": "array",
                                                    "items": {
                                                            "$ref": "#/components/schemas/"
                                                                + self.data_type
                                                            },
                                                        }
                                                    },
                                                }
                                            }
                                else:
                                    if not isLikelyAnArray and "{" not in self.data_type:
                                        res[self.response_code] = {
                                            "description": self.description,
                                            "content": {
                                                "application/json": {
                                                    "schema": {
                                                        "type": "object",
                                                        "properties": {
                                                            self.data_type: {
                                                                "$ref": "#/components/schemas/"
                                                                    + self.data_type
                                                                },
                                                            }
                                                        },
                                                    }
                                                }
                                            }
                                    
                                    else:
                                        if self.data_type.__contains__("{"):
                                            words = self.description.split()
                                            types = config['tags']
                                            lcm_found = False  # Flag variable to track if 'lcm' is found in types
                                            for type in types:
                                                if 'lcm' in type:
                                                    self.data_type = 'AppLcmOpOccSubscriptionRequest'
                                                    lcm_found = True
                                                    break
                                            if not lcm_found:
                                                words = self.description.split()

                                                for word in words:
                                                    if (
                                                        len(word) > 13
                                                        and word.find("subscription")
                                                        and word != "NotificationSubscription"
                                                    ):
                                                        if word[-1] == ".":
                                                            self.data_type = word[:-1]
                                                        else:
                                                            self.data_type = word
                                                        break                                             
                                            res[self.response_code] = {
                                                "description": self.description,
                                                "content": {
                                                    "application/json": {
                                                        "schema": {
                                                            "type": "object",
                                                            "properties": {
                                                                self.data_type: {
                                                                    "$ref": "#/components/schemas/"
                                                                    + self.data_type
                                                                }
                                                            },
                                                        }
                                                    }
                                                },
                                            }
                                        else:
                                            res[self.response_code] = {
                                                "description": self.description,
                                                "content": {
                                                    "application/json": {
                                                        "schema": {
                                                            "type": "object",
                                                            "properties": {
                                                                self.data_type: {
                                                                    "$ref": "#/components/schemas/"
                                                                    + self.data_type
                                                                }
                                                            },
                                                        }
                                                    }
                                                },
                                            }

                            # If the response_code is not 200 or 201, add a dictionary to res with the $ref key
                            else:
                                res[self.response_code] = {
                                    "$ref": "#/components/responses/"
                                    + self.response_code
                                }
                        # If the response_code is not in the list of valid codes, add a dictionary of request
                        else:
                            if self.cardinality == "0..N":
                                self.cardinality = "array"
                                request = {
                                    "description": self.description,
                                    "required": self.is_required,
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "type": self.cardinality,
                                                    "items": {
                                                        self.data_type: {
                                                            "$ref": "#/components/schemas/"
                                                            + self.data_type
                                                        }
                                                    },
                                                },
                                            }
                                        }
                                    },
                                }
                            else:
                                if self.data_type.__contains__("{"):
                                    words = self.description.split()
                                    for word in words:
                                        if (
                                            len(word) > 13
                                            and word.find("subscription")
                                            and word != "NotificationSubscription"
                                        ):
                                            if word[-1] == ".":
                                                self.data_type = word[:-1]
                                            else:
                                                self.data_type = word
                                            break
                                    request = {
                                        "description": self.description,
                                        "content": {
                                            "application/json": {
                                                "schema": {
                                                    "type": "object",
                                                    "properties": {
                                                        self.data_type: {
                                                            "$ref": "#/components/schemas/"
                                                            + self.data_type
                                                        }
                                                    },
                                                }
                                            }
                                        },
                                    }
                                else:
                                    request = {
                                        "description": self.description,
                                        "required": self.is_required,
                                        "content": {
                                            "application/json": {
                                                "schema": {
                                                    "type": "object",
                                                    "properties": {
                                                        self.data_type: {
                                                            "$ref": "#/components/schemas/"
                                                            + self.data_type
                                                        }
                                                    },
                                                }
                                            }
                                        },
                                    }
            else:
                if self.description != '':
                    request = {
                        "description": self.description,
                        "content": {"application/json": {}},
                        "required": False,
                    }

        # Returns a tuple containing the res and request dictionaries.
        return res, request