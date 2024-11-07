#!/bin/bash

# Keep-alive script for GitHub Codespaces
# This script sends a harmless command (e.g., printing the current time) every X seconds

INTERVAL=60  # Set interval in seconds (e.g., 300 seconds = 5 minutes)

while true; do
  echo "Keeping session alive: $(date)"
  sleep $INTERVAL
done
#
