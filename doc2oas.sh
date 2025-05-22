#!/bin/bash

# useful paths
SPECDIR_MEC=mec_specs
SPECDIR_NFV=nfv_specs
CONFIGDIR=configs
OUTDIR=out

SPEC=$1

# Command usage
usage() {
    echo "
    NAME
        doc2oas - Generates a base OAS3 YAML file from the DOCX specification

    SYNOPSIS
        doc2oas <SPEC>

    SPEC
        Supported values:  mec010-2, mec011, mec012, mec013, mec014, mec015, mec016, mec021, mec028, mec029, mec030
    "
    exit 1
}

# Spec
if [ "$SPEC" == "mec010-2" ] ; then
  SPECNAME=gs_mec01002v030101p
  INFILE="${SPECDIR_MEC}/${SPECNAME}.docx"
  OUTFILE="${SPECDIR_MEC}/${SPECNAME}.yaml"
  CONFIG=("${CONFIGDIR}/mec010-2_AppGrant_config.yaml" "${CONFIGDIR}/mec010-2_AppLcm_config.yaml" "${CONFIGDIR}/mec010-2_AppPkgMgmt_config.yaml")

elif [ "$SPEC" == "mec011" ] ; then
  SPECNAME=gs_mec011v030101p
  INFILE="${SPECDIR_MEC}/${SPECNAME}.docx"
  OUTFILE="${SPECDIR_MEC}/${SPECNAME}.yaml"
  CONFIG=("${CONFIGDIR}/mec011_AppSupp_config.yaml" "${CONFIGDIR}/mec011_SrvMgmt_config.yaml")

elif [ "$SPEC" == "mec012" ] ; then
  SPECNAME=gs_mec012v020201p
  INFILE="${SPECDIR_MEC}/${SPECNAME}.docx"
  OUTFILE="${SPECDIR_MEC}/${SPECNAME}.yaml"
  CONFIG="${CONFIGDIR}/mec012_config.yaml"

elif [ "$SPEC" == "mec013" ] ; then
  SPECNAME=gs_mec013v030101p
  INFILE="${SPECDIR_MEC}/${SPECNAME}.docx"
  OUTFILE="${SPECDIR_MEC}/${SPECNAME}.yaml"
  CONFIG="${CONFIGDIR}/mec013_config.yaml"

elif [ "$SPEC" == "mec014" ] ; then
  SPECNAME=gs_mec014v020101p
  INFILE="${SPECDIR_MEC}/${SPECNAME}.docx"
  OUTFILE="${SPECDIR_MEC}/${SPECNAME}.yaml"
  CONFIG="${CONFIGDIR}/mec014_config.yaml"

elif [ "$SPEC" == "mec015" ] ; then
  SPECNAME=gs_mec015v020201p
  INFILE="${SPECDIR_MEC}/${SPECNAME}.docx"
  OUTFILE="${SPECDIR_MEC}/${SPECNAME}.yaml"
  CONFIG=("${CONFIGDIR}/mec015_BWM_API_config.yaml" "${CONFIGDIR}/mec015_MTS_API_config.yaml")

elif [ "$SPEC" == "mec016" ] ; then
  SPECNAME=gs_mec016v020201p
  INFILE="${SPECDIR_MEC}/${SPECNAME}.docx"
  OUTFILE="${SPECDIR_MEC}/${SPECNAME}.yaml"
  CONFIG="${CONFIGDIR}/mec016_config.yaml"

elif [ "$SPEC" == "mec021" ] ; then
  SPECNAME=gs_mec021v020201p
  INFILE="${SPECDIR_MEC}/${SPECNAME}.docx"
  OUTFILE="${SPECDIR_MEC}/${SPECNAME}.yaml"
  CONFIG="${CONFIGDIR}/mec021_config.yaml"

elif [ "$SPEC" == "mec028" ] ; then
  SPECNAME=gs_mec028v020301p
  INFILE="${SPECDIR_MEC}/${SPECNAME}.docx"
  OUTFILE="${SPECDIR_MEC}/${SPECNAME}.yaml"
  CONFIG="${CONFIGDIR}/mec028_config.yaml"

elif [ "$SPEC" == "mec029" ] ; then
  SPECNAME=gs_mec029v020201p
  INFILE="${SPECDIR_MEC}/${SPECNAME}.docx"
  OUTFILE="${SPECDIR_MEC}/${SPECNAME}.yaml"
  CONFIG="${CONFIGDIR}/mec029_config.yaml"

elif [ "$SPEC" == "mec030" ] ; then
  SPECNAME=gs_mec030v030101p
  INFILE="${SPECDIR_MEC}/${SPECNAME}.docx"
  OUTFILE="${SPECDIR_MEC}/${SPECNAME}.yaml"
  CONFIG="${CONFIGDIR}/mec030_config.yaml"

elif [ "$SPEC" == "mec033" ] ; then
  SPECNAME=gs_mec033v030101p
  INFILE="${SPECDIR_MEC}/${SPECNAME}.docx"
  OUTFILE="${SPECDIR_MEC}/${SPECNAME}.yaml"
  CONFIG="${CONFIGDIR}/mec033_config.yaml"

elif [ "$SPEC" == "mec040" ] ; then
  SPECNAME=gs_mec040v030101p
  INFILE="${SPECDIR_MEC}/${SPECNAME}.docx"
  OUTFILE="${SPECDIR_MEC}/${SPECNAME}.yaml"
  CONFIG="${CONFIGDIR}/mec040_config.yaml"

else
  echo "ERROR: Invalid SPEC"
  usage
fi

## FUNCTIONS ##
gen-spec(){
  
  for configfile in ${CONFIG[@]}; do

    echo ""
    echo "### Parameters"
    echo "   Input file:  ${INFILE}"
    echo "   Config file: ${configfile}"
    echo "   Output file: $OUTDIR/$SPECNAME.yaml"

    echo ""
    echo "### Converting file"

    cd src/
    
    # Check if Python is available
    if command -v python3 &> /dev/null; then
        PYTHON_CMD=python3
    elif command -v python &> /dev/null; then
        PYTHON_CMD=python
    else
        echo "Error: Python is not installed or not in PATH."
        cd ..
        exit 1
    fi

    # Run the Python script and check its exit status
    if ! $PYTHON_CMD main.py "../$INFILE" "../$configfile"; then
        echo "Error: Python script failed. Check the error message above for details (e.g., syntax error)."
        cd ..
        echo "### ERROR: Output file $OUTFILE was not generated due to the Python script failure."
        continue  # Move to the next config file if applicable
    fi
    cd ..

    # Check if the output file was generated
    if [ -f "$OUTFILE" ]; then
        echo ""
        echo "### Post-processing $OUTFILE"
        ./postProcessing.sh "$OUTFILE"
        echo ""
        WORDTOREMOVE="_config"
        CLEAN_OUTFILE=$(echo "${configfile:8}" | sed s/"$WORDTOREMOVE"//)
        if [[ $CLEAN_OUTFILE == *[_]* ]]; then
            NEW_OUTFILE="_${CLEAN_OUTFILE#*_}"
        else
            NEW_OUTFILE=".${CLEAN_OUTFILE#*.}"
        fi
        echo "### OAS YAML file is generated to $OUTDIR/$SPECNAME$NEW_OUTFILE"
        mv $OUTFILE "$OUTDIR/$SPECNAME$NEW_OUTFILE"
    else
        echo "### ERROR: Output file $OUTFILE was not generated. Check the Python script execution."
    fi
  done
}

## main ##
gen-spec
