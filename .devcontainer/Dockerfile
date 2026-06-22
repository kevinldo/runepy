FROM mcr.microsoft.com/devcontainers/python:3.14

RUN apt-get update \
    && apt-get install -y postgresql-client \
    && rm -rf /var/lib/apt/lists/*