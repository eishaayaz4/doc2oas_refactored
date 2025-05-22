#!/bin/python3
"""
Test data_definition.py
"""
import difflib
import textwrap
from data_definition import (
    get_oas_data_definition_obj,
    next_sibling_field_idx,
    get_oas_for_api_data_definition,
    DICT_FOR_REF_DM,
    get_oas_for_query_param_data_definition,
)
from utils import INLINED_TYPE, yaml_dump


def test_data_type_with_1_lvl_inline():
    """
    Test inlined fields
    """

    TAB = [
        ["lvl1_field_1", INLINED_TYPE, "0..N", "My Description"],
        [">lvl2_field_1", "String", "1", "My Description"],
        ["lvl1_field_2", "Enum", "1", "My Description"],
    ]

    expected_output = """\
    x-etsi-ref: 1.1.1
    type: object
    properties:
    lvl1_field_1:
        type: array
        items:
        $ref: '#/components/schemas/Lvl1_field_1'
    lvl1_field_2:
        type: string
        description: My Description
        enum:
        - SEE_DESCRIPTION
    required:
    - lvl1_field_2"""
    expected_referenced_obj = {
        "Lvl1_field_1": {
            "description": "My Description",
            "type": "object",
            "minItems": 0,
            "properties": {
                "lvl2_field_1": {
                    "description": "My Description",
                    "type": "string",
                }
            },
            "required": ["lvl2_field_1"],
        }
    }

    res = get_oas_data_definition_obj(TAB, "1.1.1", 0)
    output = yaml_dump(res)
    output = textwrap.dedent(output).strip()
    output_lines = [line.lstrip() for line in output.splitlines()]
    expected_lines = [line.lstrip() for line in expected_output.splitlines()]

    # Join the lines into a single string
    output_cleaned = '\n'.join(output_lines)
    print("output_cleaned:")
    print(repr(output_cleaned))
    expected_cleaned = '\n'.join(expected_lines)
    print("expected_cleaned:")
    print(repr(expected_cleaned))
    # Now, compare the cleaned strings
    assert output_cleaned == expected_cleaned
    assert DICT_FOR_REF_DM == expected_referenced_obj


def test_next_sibling_field_idx_1_lvl():
    table = [
        ["lvl1_field_1", INLINED_TYPE, "1", "My Description"],
        [">lvl2_field_1", "String", "1", "My Description"],
        ["lvl1_field_2", "String", "1", "My Description"],
    ]

    assert next_sibling_field_idx(table, 1, 0) == 2


def test_next_sibling_field_idx_2_lvl():
    table = [
        ["lvl1_field_1", INLINED_TYPE, "1", "My Description"],
        [">lvl2_field_1", "String", "1", "My Description"],
        [">lvl2_field_2", INLINED_TYPE, "1", "My Description"],
        [">>lvl3_field_1", "String", "1", "My Description"],
        ["lvl1_field_2", INLINED_TYPE, "1", "My Description"],
        [">lvl2_field_3", "String", "1", "My Description"],
        ["lvl1_field_3", "String", "1", "My Description"],
    ]

    assert next_sibling_field_idx(table, 1, 0) == 4
    assert next_sibling_field_idx(table, 3, 1) == 4


# ########### Test cases related to API Definitions implementation #################
# #################################################################################


def test_get_oas_for_api_data_definition():
    TAB = [
        ["ApInfo", "0..N", "200 OK", "Test Description."],
        ["ProblemDetails", "See annex E of [10]", "4xx/5xx", "Test Description."],
        ["ProblemDetails", "1", "400 Bad Request", "Test Description."],
    ]

    expected_dict = ({'200': {'description': 'Test Description.', 'content': {'application/json': {'schema': {'type': 'array', 'items': {'$ref': '#/components/schemas/ApInfo'}}}}}, '4xx': {'$ref': '#/components/responses/4xx'}, '400': {'$ref': '#/components/responses/400'}}, {})

    res = get_oas_for_api_data_definition(TAB)
    assert res == expected_dict


def test_get_oas_for_query_param_data_definition():
    TAB = [
        ["filter", "int32", "0..N", "Testing common datatype."],
        ["Apinfo", "Apinfo", "0..1", "Testing Non-common datatype."],
    ]

    expected_dict = {
        "Query.Filter": {
            "description": "Testing common datatype.",
            "name": "filter",
            "cardinality": "0..N",
            "in": "query",
            "required": False,
            "x-exportParamName": "Query.Filter",
            "schema": {"type": "array", "items": {"type": "integer"}},
        },
        "Query.Apinfo": {
            "description": "Testing Non-common datatype.",
            "name": "apinfo",
            "cardinality": "0..1",
            "in": "query",
            "required": False,
            "x-exportParamName": "Query.Apinfo",
            "schema": {"$ref": "#/components/schemas/Apinfo"},
        },
    }
    response = get_oas_for_query_param_data_definition(TAB, False)
    assert response == expected_dict
