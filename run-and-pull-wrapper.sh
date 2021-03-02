#!/bin/bash

# * WHERE TO RUN: my linux server infotinks.com

# * WHAT THIS DOES:
# call git pull to update code base with latest remote git
# calls ./run.sh & and shows PIDs and follows log

cd /var/www/covid19/
echo "* Pulling latest updates from git on remote server"
git pull
echo "* Starting Remote Plot Generation"
./run.sh &
sleep 1
PSCMD='"'"'ps aux | grep -E "run.sh|covid19plot|county-plot" | grep -vE "grep|defunc"'"'"'
PSOUT=$(/bin/bash -c "$PSCMD")
PIDS=$(echo "$PSOUT" | awk '"'"'{print $2}'"'"')
echo "* Background Job PIDs: "$(echo "$PIDS")" <-- log in to `hostname` and kill those PIDs to stop it"
echo "# $PSCMD"
echo "$PSOUT"
echo "* Following Log File - cancel the follow with ctrl-c, the job will still run"
LOGFILE=$(ls -1tr | grep 'run.*out' | tail -1)
tail -n 1000 -F $(ls -1tr | grep 'run.*out' | tail -1)