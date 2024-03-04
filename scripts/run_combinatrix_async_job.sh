#!/bin/sh
script_dir=$(dirname "$(readlink -f "$0")")
export PYTHONPATH=$script_dir/../lib:$PYTHONPATH

python -u $script_dir/../lib/combinatrix/CombinatrixServer.py $1 $2 $3
