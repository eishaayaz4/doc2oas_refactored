#!/bin/python3
"""
Unit test suite for data_field.py
"""

from cgi import test
import yaml
from data_field import DataField, QueryTableRow

from utils import INLINED_TYPE, yaml_dump


def test_yaml_lib():
    """
    Test the YAML dump function
    """

    expected_yaml = """obj:
  description: My Description
  type: string
  x-etsi-mec-cardinality: '1'
  x-etsi-mec-origin-type: String
"""
    assert yaml_dump(yaml.load(expected_yaml)) == expected_yaml


def test_data_field_capital_string():
    """
    Test creation of a data field with type String
    """
    row = ["Version", "String", "1", "My Description"]

    expected_yaml = """obj:
  description: My Description
  type: string
"""

    andf = DataField(
        row[0],
        row[1],
        row[2],
        row[3],
    )
    assert andf.is_required
    assert not andf.is_array
    assert andf.name == "Version"
    assert andf.clean_type == "string"
    assert andf.description == "My Description"
    var = yaml_dump({"obj": andf.to_dict()})
    assert var == expected_yaml


def test_data_field_inlined():
    """
    Test creation of a data field with type String
    """
    row = ["Version", INLINED_TYPE, "1", "My Description"]

    expected_yaml = """obj:
  description: My Description
  type: object
"""

    ndf = DataField(
        row[0],
        row[1],
        row[2],
        row[3],
    )
    assert ndf.is_required
    assert ndf.name == "Version"
    assert ndf.clean_type == "object"
    assert ndf.description == "My Description"
    assert ndf.has_inlined
    var = yaml_dump({"obj": ndf.to_dict()})
    assert var == expected_yaml


def test_data_field_uris():
    """
    Test creation of a data field with type String
    """
    row = ["CallbackUri", "URI", "1", "My Description"]

    expected_yaml = """obj:
  description: My Description
  type: string
  format: uri
"""

    ndf = DataField(
        row[0],
        row[1],
        row[2],
        row[3],
    )
    assert ndf.is_required
    assert ndf.name == "CallbackUri"
    assert ndf.clean_type == "string"
    assert ndf.description == "My Description"

    var = yaml_dump({"obj": ndf.to_dict()})
    assert var == expected_yaml


def test_data_field_float():
    """
    Test creation of a data field with type String
    """
    row = ["Myfield", "Float", "1", "My Description"]

    expected_yaml = """obj:
  description: My Description
  type: number
  format: float
"""

    ndf = DataField(
        row[0],
        row[1],
        row[2],
        row[3],
    )
    assert ndf.is_required
    assert ndf.name == "Myfield"
    assert ndf.clean_type == "number"
    assert ndf.description == "My Description"
    var = yaml_dump({"obj": ndf.to_dict()})
    assert var == expected_yaml


def test_data_field_inherited_attributes():
    """
    Test creation of a data field with type String
    """
    row = ["(inherited attributes)", "", "", "All attributes inherited from Cpd."]

    expected_yaml = """obj:
  description: All attributes inherited from Cpd.
  type: object
"""

    ndf = DataField(
        row[0],
        row[1],
        row[2],
        row[3],
    )
    assert ndf.is_required
    assert ndf.name == "inherited_attributes"
    assert ndf.clean_type == "object"
    assert ndf.description == "All attributes inherited from Cpd."
    var = yaml_dump({"obj": ndf.to_dict()})
    assert var == expected_yaml


def test_data_field_not_specified():
    """
    Test creation of a data field with type String
    """
    row = ["Mydata", "Not specified", "1", "This is not specified."]

    expected_yaml = """obj:
  description: This is not specified.
  type: object
"""

    ndf = DataField(
        row[0],
        row[1],
        row[2],
        row[3],
    )
    assert ndf.is_required
    assert ndf.name == "Mydata"
    assert ndf.clean_type == "object"
    assert ndf.description == "This is not specified."
    var = yaml_dump({"obj": ndf.to_dict()})
    assert var == expected_yaml


def test_data_field_array():
    """
    Test creation of a data field with type String
    """
    rows = [
        ["Myfield", "MyType", "0..N", "My Description"],
    ]

    for row in rows:
        expected_yaml = """obj:
  description: {}
  type: array
  minItems: {}
  items:
    $ref: '#/components/schemas/{}'
""".format(
            row[3], row[2].split("..")[0], row[1]
        )

        ndf = DataField(row[0], row[1], row[2], row[3])
        assert ndf.name == row[0]
        assert ndf.is_array
        assert ndf.clean_type == "array"
        assert ndf.description == row[3]
        assert ("items", {"$ref": "#/components/schemas/" + row[1]}) in ndf.extras
        var = yaml_dump({"obj": ndf.to_dict()})
        assert var == expected_yaml


# # ########### Test cases related to API Definitions implementation #################
# # #################################################################################


def test_class_TableRow():
    # code to test TableRow() class
    input = [
        "location_info",
        "String",
        "1",
        "Comma separated list of locations to identify a cell of a base station or a particular geographical area,",
    ]
    expected_value = """obj:
  Query.Location_info:
    description: Comma separated list of locations to identify a cell of a base station or a particular geographical area,.
    name: location_info
    cardinality: '1'
    in: query
    required: true
    x-exportParamName: Query.Location_info
    schema:
      type: string
    """
    test_1 = QueryTableRow(input[0], input[1], input[2], input[3])
    var = yaml_dump({"obj": test_1.to_dict_for_query_param_def()})
    assert var.strip() == expected_value.strip()
