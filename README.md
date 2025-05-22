# doc2oas tool

doc2oas tool generates a baseline OAS3 data model (yaml) from the specification document (docx).

It parses the Data object tables from the specification document and creates the corresponding data model objects to the OAS3 yaml file.

## How to use the doc2oas tool

### Step 1: Install required python3 libraries

```
# Install python using the following command.
# If python is already there, then you can skip this step.

sudo apt-get install python3

# Install the dependency packages

python3 -m pip install -r requirements.txt
```

### Step 2: Create the config file for the specification document

This file provides information about the specification document format and external types.

Specifications depend on external data types; the config file is used to define these.  

The config file has the following sections:

- data_model_headings: `data_model_headings` dictionary further contains nested headings (headings1, headings2, and so on) identifying the document sections from where the Data model tables start and stop. E.g. in the MEC012 specification data definition starts in the 6th section and till the 7th (pay extra attention to the word case and numbers).
- api_def_headings: The `api_def_headings` dictionary includes nested headings such as headings1, headings2, and so on, which identify the document sections where the API definition tables are located. For example, in the MEC012 specification, the API definition table can be found between the `7 API definition` and `7.3 Resource: rab_info` sections.  (pay extra attention to the word case and numbers).
- fake_data_types: Not used so keep this false.
- manual_types: This is used to add schema for data objects not present in the document. These will get directly added to the generated YAML file.

### Step 3: Running doc2oas
The tool is invoked from a shell script called `doc2oas.sh`

Usage
```
./doc2oas.sh
    NAME
        doc2oas - Generates a base OAS3 YAML file from the DOCX specification

    SYNOPSIS
        doc2oas <SPEC>

    SPEC
        Supported values:  mec010-2, mec011, mec012, mec013, mec014, mec015, mec016, mec021, mec028, mec029, mec030, mec033, mec040
```
Example:
```
# Generate mec012 OAS3 baseline
./doc2oas.sh mec012
```
<br>
If any MEC specification document has more than 1 API there will be a separate config file for each API and a separate OAS YAML file will be generated for every API when `doc2oas.sh` is invoked. For example, MEC 010-2 V3.1.1 have 3 APIs, and MEC 015 V2.2.1 have 2 APIs, in this case, each API has its own config file and separate OAS YAML files will be generated for each API.

<br>

> To understand how to update or add a new config file when new Data Models or APIs are added in the specification, please refer to [this link](./configs/README.md#when-to-update-or-add-a-new-config).

> To understand how to update the `doc2oas.sh` script to generate multiple OAS YAML files from a single specification document, please refer to [this link](./configs/README.md#add-a-new-config-file).

<br>

Repo structure
```
.
├── configs             # Config files
├── doc2oas.sh          # Main script
├── LICENSE
├── mec_specs           # ETSI MEC Specifications
├── nfv_specs           # ETSI NFV Specifications
├── out                 # Generated OAS files
├── postProcessing.sh
├── README.md
├── requirements.txt    # Tool dependencies
├── src                 # src code
├── test.sh             # Contains testcases
```

## WARNING
The doc2oas tool is not 100% accurate so there might be some mismatch or missing attributes in the generated OAS3.

It is recommended to meticulously inspect the generated files.

## Minor issues that can be occured
1) Note: Config files should be specific for each version of a MEC spec, as range of Data Models and API Definitions given in the current config files can be different in latest/previous specs.

2) Document sometimes misspelled data models or resources resulting in non-existing types or wrong referencing.

3) The ```summary``` tag under endpoint's HTTP method wont be populated if the ```HTTP methods overview``` table is missing in the MEC spec.

4) Endpoints and their respective HTTP methods under ```Paths``` tag should be reviewed thoroughly. Tool sometimes can miss population of those HTTP methods whose table structure is quite different from the standard structure defined in MEC specs.

5) The tool works correctly with the current format of the MEC specs However, if there are any inconsistencies in the format of the specs, the resulting OAS may have some issues that will need to be fixed manually.

6) Sometimes, the MEC specs refer to certain attributes that actually exist in other specification documents, such as NFV IFA documents, and etc. This can lead to incorrect referencing. To address this issue, the relevant data models need to be manually added to the corresponding configuration files.