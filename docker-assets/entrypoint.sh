#!/bin/bash


## Allow the user to create a autorun-file to install more packages via apt for example
if [ -f /app/autorun.sh ]; then
  if [ ! -f /app/.autorun_ok ]; then
    /app/autorun.sh
    touch /app/.autorun_ok
  fi
fi

minitor --config /app/config.yml