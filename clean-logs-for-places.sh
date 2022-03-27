#!/bin/bash

# what this does: cleans stale/bad output files, run*out, this only needs to look for stale files in covid19 dir and not any of the subdirs. this is important for parse.sh to work, as it might choke on these bad output files
# where to run: run in covid19 root directory
# how to run: run without options to see which files are stale, and run with -c to delete them as well
# ./clean-logs-for-places.sh     # just shows the stale output files if they exist
# ./clean-logs-for-places.sh -c  # shows and deletes stale files

EXTRA_CMD=""

echo "* Stale/bad output file finder. Looks for stale or bad run.*out files in covid19 root directory; not recursively"

if [[ $1 == '-c' ]]; then
   EXTRA_CMD='echo "Deleting $i"; rm -vf "$i";'
   echo "* Performing cleaning operation"
else
   echo "* Dry run. Not cleaning. To clean add -c argument."
fi

for i in run*out; do
    grep -q -- "- end" $i && { 
        echo "Found stale output file: $i";
    } || {
        echo "Found stale output file: $i";
        eval "$EXTRA_CMD";
    }
done | grep -v Found

echo "* Done"

exit 0
