The tool works as follows:

## Step 1: Uploading the files 

In the uploaded Document it searches for headings according to the config file:

* data_model_headings: data_model_headings dictionary further contains nested headings (headings1, headings2, and so on) identifying the document sections from where the Data model tables start and stop. E.g. in the MEC012 specification data definition starts in the 6th section and till the 7th (pay extra attention to the word case and numbers).
* api_def_headings: The api_def_headings dictionary includes nested headings such as headings1, headings2, and so on, which identify the document sections where the API definition tables are located. For example, in the MEC012 specification, the API definition table can be found between the 7 API definition and 7.3 Resource: rab_info sections.  (pay extra attention to the word case and numbers).
* fake_data_types: Not used so keep this false.
* manual_types: This is used to add schema for data objects not present in the document. These will get directly added to the generated YAML file.

## Step 2, generation of data types

For each of the section after the specified headings the tool searches for tables with the following properties:

* Data model definitions tables that match certain number of columns with a specific header name. I.e. the table contains 4 columns with the headers Attribute name, Data type, Cardinality and Description.

* API definitions table (including API overview tables, related query parameter tables, etc...) that match certain number of columns with a specific header name. I.e. an API definition table contains 4 columns with the headers Request body, Data Type, Cardinality and Remarks.


		Note: Both Data model definitions and API definitions tables properties (columns and header names) can be extended to other configurations
		
## Step 3: Generation of files

The set of generated definitions is written to a yaml file named as the uploaded specification Word document. A conversion log file is provided alongside.

## Step 4: Download

The files are archived in a zip file named `oas_defs.zip` which is served as a response.