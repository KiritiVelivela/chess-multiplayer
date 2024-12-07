# Use the official Python base image
FROM python:3.9.10-slim-bullseye
# Install Redis server and supervisord
RUN apt-get update && apt-get install -y \
    redis-server \
    supervisor \
    gcc musl-dev libpq-dev \
    netcat postgresql-client mime-support \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
# WORKDIR /

# Copy the requirements file
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /

# Make the docker_run_server.sh script executable
RUN chmod +x docker_run_server.sh

# Copy the supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose the port Daphne will run on
EXPOSE 80

# Set the entrypoint to your existing script
ENTRYPOINT ["./docker_run_server.sh"]