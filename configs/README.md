# doc2oas configs

For every API, *API definition* table and *Data Model* tables are required to be parsed to generate `paths` and corresponding `data model objects`. So, there are a few important things to be noted on how to specify config files to properly generate OAS3 yaml files.

- The `api_def_headings` dictionary further contains nested headings (headings1, headings2 and so on) identifying where the api_def_headings tables start and stop. Every config file contains `api_def_headings` for the generation of `paths`.

  For some APIs, *API definition* tables lie between two specific sections, in this case, those sections can be specified under one `headings1` section For example, the `api_def_headings` structure in `mec016_config.yaml` looks like this:
  ```yaml
  api_def_headings:
    headings1:
      - '7[ ]*API definition$'
      - '8[ ]*Authentication\, authorization and access control$'
  ```
- For some APIs, *API definition* tables may lie in different sections throughout the document. In that case, multiple `nested headings` will be needed to parse all of the required API definitions. For example, the `api_def_headings` structure in `mec010-2_AppGrant_config.yaml look like this:
  ```yaml
  api_def_headings:
    headings1:
      - 'Table 7\.2\-1\: Overview of resources and methods of MEO''s application package management on Mm1$'
      - 'Table 7\.2\-6\: Overview of resources and methods of MEO''s application life cycle management on Mm1$'
    headings2:
      - '7\.5 Resources of granting on Mm3$'
      - '7\.6 Resources of MEPM''s application lifecycle management on Mm3$'
  ```
- The `data_model_headings` dictionary further contains nested headings (headings1, headings2, and so on) identifying where the Data model starts and stops. 

  For some APIs, Data Model tables lie between two specific sections, in that case, those sections can be specified under one `headings1` section. For example, in the case of MEC016 all Data Model tables between the *Data model* and *API definition* sections have to be parsed, so the `data_model_headings` structure would look like this:

  ```yaml
  data_model_headings:
    headings1:
      - '6[ ]*Data model$'
      - '7[ ]*API definition$'
  ```
- For some APIs, Data Model tables may lie in different sections throughout the document. In that case, multiple `nested headings` will be needed to parse all of the required data models. For example, in the case of *MEC010 (v2.2.1) Application Life Cycle Management API* API-specific data models lie between *6.2.2 Application lifecycle management information model* and *6.2.3 Application package information model* sections, and common data models lie between *6.2.5 Common information model* and *6.3 Interfaces* sections. Consequently, the `data_model_headings` structure in `mec010-2_AppLcm_config.yaml` looks like this:

  ```yaml
  data_model_headings:
    headings1:
      - '6\.2\.2 Application lifecycle management information model$'
      - '6\.2\.3 Application package information model$'
    headings2:
      - '6\.2\.5 Common information model$'
      - '6\.3 Interfaces$'
  ```
>Note: Section names should be provided as regex.

## When to update or add a new config

### Update an existing config file

If new Data Model tables are added to any MEC specification document, there would be no need to fix or update the code. Only update the `data_model_headings` dictionary section of the corresponding config file.

### Add a new config file

For every API, there should be a separate config file as the Data Model tables and API definition table varies for each API. If a new API is added in any of the MEC specifications, create a config file in the _configs_ folder and assign its name to the _CONFIG_ variable under the `#spec` tag in _doc2oas.sh_ script. For example:

```sh
CONFIG=("${CONFIGDIR}/mec015_BWM_API_config.yaml" "${CONFIGDIR}/mec015_MTS_API_config.yaml")
```
and then invoke the `doc2oas.sh` script, using the command:
```sh
./doc2oas.sh mec015
```
a separate OAS YAML file will be generated for each API.