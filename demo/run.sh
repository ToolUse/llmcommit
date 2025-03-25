#!/bin/bash

# Adapted from https://docs.streamlit.io/deploy/tutorials/kubernetes

APP_PID=
stopRunningProcess() {
    # Based on https://linuxconfig.org/how-to-propagate-a-signal-to-child-processes-from-a-bash-script
    if test ! "${APP_PID}" = '' && ps -p ${APP_PID} > /dev/null ; then
       > /proc/1/fd/1 echo "Stopping ${COMMAND_PATH} which is running with process ID ${APP_PID}"

       kill -TERM ${APP_PID}
       > /proc/1/fd/1 echo "Waiting for ${COMMAND_PATH} to process SIGTERM signal"

        wait ${APP_PID}
        > /proc/1/fd/1 echo "All processes have stopped running"
    else
        > /proc/1/fd/1 echo "${COMMAND_PATH} was not started when the signal was sent or it has already been stopped"
    fi
}

trap stopRunningProcess EXIT TERM

# Add streamlit to dependencies for the demo
pip install streamlit
pip install -e . 

# First look for app.py in the same directory as this script
SCRIPT_DIR="$(dirname "$0")"
APP_PATH="$SCRIPT_DIR/app.py"

# Fall back to original path if not found
if [ ! -f "$APP_PATH" ]; then
    echo "Looking for app.py in ${HOME}/blueprint/demo/"
    APP_PATH="${HOME}/blueprint/demo/app.py"
    
    # Finally try current directory
    if [ ! -f "$APP_PATH" ]; then
        echo "Looking for app.py in current directory"
        APP_PATH="./app.py"
        
        if [ ! -f "$APP_PATH" ]; then
            echo "Error: Could not find app.py in any location"
            exit 1
        fi
    fi
fi

echo "Found app.py at: $APP_PATH"
streamlit run "$APP_PATH" &
APP_PID=$!

wait $APP_PID
