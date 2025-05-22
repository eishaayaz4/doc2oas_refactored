#!/bin/python3
"""
Utils
"""
import re
import yaml
import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

INLINED_TYPE = "Structure"

SPC = "  "


def yaml_dump(a):
    return yaml.safe_dump(a, default_flow_style=False, width=10000, sort_keys=False)


class Section:
    def __init__(self, heading, id_from, id_to):
        self.heading = heading
        self.id_from = id_from
        self.id_to = id_to


def docx_tab_to_string_matrix(tmp_elem, reverse_order=False):
    """
    Returns a matrix of strings with the text from a Docx table
    """
    res = []
    for row in tmp_elem.rows:
        row_string = []
        for cell in row.cells:
            if cell.text is not "none supported":
                row_string.append(cell.text)
        row_string.append(cell.text)
        res.append(row_string)

    if reverse_order:
        for row in res:
            tmp = row[1]
            row[1] = row[2]
            row[2] = tmp

    return res


def get_content(doc):
    """
    Returns a list of all paragraphs and tables in the Document
    """
    ret = []
    body = doc._body
    parag_count = 0
    table_count = 0
    for element in body._element:
        if isinstance(element, docx.oxml.text.paragraph.CT_P):
            ret.append(Paragraph(element, body))
            parag_count = parag_count + 1
        elif isinstance(element, docx.oxml.table.CT_Tbl):
            ret.append(Table(element, body))
            table_count = table_count + 1
        else:
            print("Non paragraph or table " + str(type(element)))
    print("Paragraphs: " + str(parag_count))
    print("Tables: " + str(table_count))
    return ret


# clean_match function checks if the headings provided matched the headings in the content
def clean_match(text, sect_to_find):
    """ """
    p = re.compile(sect_to_find)
    ws_text = text.replace("\t", " ").strip()
    if (
        ws_text.startswith("6 ")
        or ws_text.startswith("7 ")
        or ws_text.startswith("8 ")
        or ws_text.startswith("9 ")
    ):
        print("====== '" + ws_text.replace(" ", "¬") + "' ~~~ " + sect_to_find)
        print(repr(p.match(ws_text)))
    return p.match(ws_text)


def heading_matches(elem, sect_to_find):
    """ """
    return isinstance(elem, Paragraph) and clean_match(elem.text, sect_to_find) != None


def find_sect(sect_to_find, start_idx, doc_content):
    """
    Returns the index in the doc_content list to the first paragraph
    or heading of the section with title sect_to_find,
    starting the research from start_idx
    """
    while start_idx < len(doc_content):
        my_elem = doc_content[start_idx]
        if heading_matches(my_elem, sect_to_find):
            break
        start_idx = start_idx + 1

    print("FOUND " + sect_to_find + " at " + str(start_idx))
    return start_idx


def find_all_sections(heading_pairs, content):
    """
    Returns a list of Section objects according to the list of headings regex provided
    Find all sections in the document content between specified pairs of headings.

    Args:
        heading_pairs (list of lists): Each sublist contains [start_heading, end_heading] regex patterns.
        content (list): List of document elements (paragraphs and tables).

    Returns:
        list: List of Section objects representing the sections between each pair of headings.
    """

    sects = []
    # Loop through each pair of headings
    for start_heading, end_heading in heading_pairs:
        start_idx = None
        for i, element in enumerate(content):
            if heading_matches(element, start_heading):
                start_idx = i
            elif heading_matches(element, end_heading) and start_idx is not None:
                sects.append(Section(start_heading, start_idx, i))
                start_idx = None  # Reset to allow finding additional sections if headings repeat
    return sects


########### Functions related to API Definitions implementation #################
#################################################################################


def docx_tab_to_string_matrix_for_query_param_def(tmp_elem, reverse_order=False):
    """
    Converts the content of table from specification document into string matrix
    @param tmp_elem contains the text of Docx table
    @param reverse_order if True, swaps the second and third elements in each row
    @return string_matrix returns a matrix of strings with the text from a Docx table
    """
    # Initialize an empty list to hold the string matrix
    string_matrix = []
    for row in tmp_elem.rows:
        # Initialize an empty list to hold the string values for the current row
        row_string = []
        for cell in row.cells:
            row_string.append(cell.text)
        string_matrix.append(row_string)

    # To check reverse_order flag is True
    if reverse_order:
        for row in string_matrix:
            # Swap the second and third elements in the current row
            tmp = row[1]
            row[1] = row[2]
            row[2] = tmp

    return string_matrix


def docx_tab_to_string_matrix_for_api_def(tmp_elem, reverse_order=False):
    """
    Converts the content of table from specification document into string matrix
    @param tmp_elem contains the text of Docx table
    @param reverse_order if True, swaps the second and third elements in each row
    @return string_matrix returns a matrix of strings with the text from a Docx table
    """
    string_matrix = []
    for row in tmp_elem.rows:
        # Create an empty list called row_string to store the text from each cell in the row
        row_string = []
        for cell in row.cells:
            row_string.append(cell.text)
        string_matrix.append(row_string)

    # If reverse_order is True, swap the second and third columns of the string matrix
    if reverse_order:
        for row in string_matrix:
            tmp = row[1]
            row[1] = row[2]
            row[2] = tmp

    # Remove the first column from each row of the string matrix
    i = 0
    while i < len(string_matrix):
        del string_matrix[i][0]
        i = i + 1

    # If the first cell in a row is empty, replace it with the value from the previous row
    j = 0
    while j < len(string_matrix):
        if string_matrix[j][0] == "":
            string_matrix[j][0] = string_matrix[j - 1][0]
        j = j + 1
    return string_matrix


def populate_callbacks(callbacks, multiple_remarks, list):
    """
    This function populates the callback section.

    Args:
        callbacks: Nested Dictionary exposing the Callbacks key.
        multiple_remarks: Boolean to check if there are multiple subscription types.
        list: One or multiple Subscription types.
    Returns:
        callbacks['notification']: Populated Callbacks Section
    """
    responses = {
        "204": {"description": "No content"},
        "404": {"description": "Not found"},
    }
    if not multiple_remarks and len(list) > 1:
        schema_ref = {"$ref": "#/components/schemas/{}".format(list[1])}
        request_body = "{$request.body#/" + list[1] + ".callbackReference}"
    elif not multiple_remarks and list:
        schema_ref = {"$ref": "#/components/schemas/{}".format(list[0])}
        request_body = "{$request.body#/" + list[0] + ".callbackReference}"
    else:
        schema_ref = {
            "oneOf": [
                {"$ref": "#/components/schemas/{}".format(remark.strip())}
                for remark in list[1:]
            ]
        }
        request_body = "{$request.body#/callbackReference}"
    callbacks["notification"] = {
        "{$request.body#/callbackUri}": {
            "post": {
                "summary": "Callback POST used to send a notification",
                "description": "Subscription notification",
                "operationId": "notificationPOST",
                "requestBody": {
                    "description": "Subscription notification",
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {"subscriptionNotification": schema_ref},
                            }
                        }
                    },
                },
                "responses": {
                    '204': {'description': "No content"},
                    '404': {'description': "Not found"},
                },
            }
        }
    }

    return callbacks["notification"]
