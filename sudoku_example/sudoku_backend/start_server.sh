#!/bin/sh
echo "Running DB Migrations, if needed..."
python manage.py makemigrations
python manage.py migrate

# Check the status of redis-server
if sudo service redis-server status | grep -q "redis-server is running"; then
    echo "Redis server is already running."
else
    echo "Redis server is not running. Starting Redis server..."
    sudo service redis-server start
    
    # Confirm if Redis started successfully
    if sudo service redis-server status | grep -q "redis-server is running"; then
        echo "Redis server started successfully."
    else
        echo "Failed to start Redis server."
        exit
    fi
fi

echo "Collecting static files..."
echo "yes" | python manage.py collectstatic

echo "Starting WSGI / ASGI Server..."
daphne -p 80 sudoku.asgi:application
