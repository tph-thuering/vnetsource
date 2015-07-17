#! /bin/bash

RUN_MANAGE_PY="python ../../../manage.py"
INSPECTDB_OUT=models-inspectdb.py
INSPECTDB_CANONICAL=models-canonical-inspectdb.py
CANONICAL=models-canonical.py

printf "Inspecting database for data_services tables...\n"
$RUN_MANAGE_PY selective_inspectdb --regex '^dim_' '^fact_(?!data)' '^lut_' '^gis_' > $INSPECTDB_OUT
printf '  Wrote data models to "%s"\n' $INSPECTDB_OUT

printf "Making canonical form of data models from database...\n"
$RUN_MANAGE_PY canonical_models --file $INSPECTDB_OUT > $INSPECTDB_CANONICAL
printf '  Wrote data models to "%s"\n' $INSPECTDB_CANONICAL

printf "Making canonical form of data models in models.py ...\n"
$RUN_MANAGE_PY canonical_models --file ../../models.py > $CANONICAL
printf '  Wrote canonical form of models.py to "%s"\n' $CANONICAL
