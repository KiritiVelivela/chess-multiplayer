#!/bin/sh
cd chess_game
# Exit on error
set -e
# Start supervisord to manage processes
exec /usr/bin/supervisord -n