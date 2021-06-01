#!/bin/bash

# run in covid19 root directory
# run -c option to clean otherwise just shows

EXTRA_CMD=""

if [[ $1 == '-c' ]]; then
   EXTRA_CMD='echo "Deleting $i"; rm -vf "$i";'
   echo "Performing cleaning operation"
else
   echo "Dry run. Not cleaning. To clean add -c argument."
fi

for i in run*out; do
    grep -q -- "- end" $i && { 
        echo "Found at $i";
    } || {
        echo "Missing at $i";
        eval "$EXTRA_CMD";
    }
done | grep -v Found

exit 0
