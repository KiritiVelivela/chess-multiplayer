
FROM python:3.9.10-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    gcc musl-dev libpq-dev \
    netcat postgresql-client mime-support \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the Django project code into the container
COPY . ./

# Expose the port (Cloud Run uses the PORT environment variable)
# ENV PORT 8000
# EXPOSE 8000
# WORKDIR /chess_game

# CMD exec daphne -b 0.0.0.0 -p 8000 backend.asgi:application
RUN chmod +x docker_run_server.sh
EXPOSE 80
ENTRYPOINT ["./docker_run_server.sh"]