#!/bin/sh
echo "Removing temp files..."
rm -rf /kb/module/work/tmp/* || true
echo "...done removing temp files."

current_dir=$(dirname "$(readlink -f "$0")")
export KB_DEPLOYMENT_CONFIG="$current_dir"/deploy.cfg
export PYTHONPATH="$current_dir"/../lib:"$PYTHONPATH"

# N.b. if running the data fetch tests, you will need a valid KBase dev token

# collect coverage data
pytest \
    --cov=lib/combinatrix \
    --cov-config=.coveragerc \
    --cov-report=html \
    --cov-report=xml \
    test/
