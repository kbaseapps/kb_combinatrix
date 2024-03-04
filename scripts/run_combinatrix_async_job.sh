#!/bin/sh
script_dir=$(dirname "$(readlink -f "$0")")
export PYTHONPATH=$script_dir/../lib:$PYTHONPATH

echo looking for $script_dir/../lib/combinatrix/CombinatrixServer.py

if [ -f "$script_dir/../lib/combinatrix/CombinatrixServer.py" ]; then
    echo "The file exists."
else
    echo "The file does not exist."
fi

python -u $script_dir/../lib/combinatrix/CombinatrixServer.py $1 $2 $3
