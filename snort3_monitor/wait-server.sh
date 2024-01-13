#!/bin/bash


if [ -z "$1" ]; then
  echo "Define script name."
  exit 1
fi

script_to_run=$1

while [ -z "`ss -tulpn | grep 0.0.0.0:8000`" ]; do
  echo 'Waiting server to start ...'
  sleep 1
done

python3 "$script_to_run"
