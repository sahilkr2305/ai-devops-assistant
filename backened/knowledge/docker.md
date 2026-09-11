Docker

What is Docker?

Docker is a containerization platform that packages an application and its dependencies into a portable container.

A container includes the application, libraries, configuration, and runtime dependencies needed to run the application consistently across environments.

Important Docker Concepts

Image

A Docker image is a read-only template used to create containers.

Example:
docker pull nginx

Container

A container is a running instance of a Docker image.

Example:
docker run -d -p 8080:80 nginx

This runs an Nginx container in detached mode and maps port 8080 on the host to port 80 inside the container.

Dockerfile

A Dockerfile contains instructions for building a Docker image.

Example:
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]

Common Docker Commands

Check Docker version:
docker --version

List running containers:
docker ps

List all containers:
docker ps -a

List images:
docker images

Pull an image:
docker pull nginx

Build an image:
docker build -t myapp .

Run a container:
docker run -d --name myapp myapp

Stop a container:
docker stop myapp

Start a stopped container:
docker start myapp

Remove a container:
docker rm myapp

Remove an image:
docker rmi myapp

View container logs:
docker logs myapp

Execute a command inside a running container:
docker exec -it myapp /bin/bash

Docker Port Mapping

The syntax is:
docker run -p HOST_PORT:CONTAINER_PORT IMAGE

Example:
docker run -d -p 8080:80 nginx

Here:
8080 is the host port.
80 is the container port.
Requests to localhost:8080 are forwarded to port 80 inside the container.

Docker Volumes

Volumes provide persistent storage for containers.

Create a volume:
docker volume create mydata

Run a container using the volume:
docker run -d --name database -v mydata:/data myimage

Volumes are useful when application data must survive container removal.

Docker Networks

Docker networks allow containers to communicate with each other.

Create a network:
docker network create app-network

Run a container on the network:
docker run -d --name backend --network app-network backend-image

Another container on the same network can communicate with the backend using the hostname:
backend

Docker Compose

Docker Compose is used to define and run multi-container applications.

Example:
services:
  backend:
    build: .
    ports:
      - "8000:8000"
  database:
    image: postgres:16

Start the application:
docker compose up -d

Stop the application:
docker compose down

Docker Troubleshooting

Container immediately stops:
Check the logs:
docker logs <container-name>

Port already in use:
Find the process using the port and either stop it or choose another host port.

Example:
docker run -p 8081:80 nginx

Container cannot communicate with another container:
Check available Docker networks:
docker network ls

Inspect a network:
docker network inspect <network-name>

Docker Best Practices

Use small base images when practical.
Do not store secrets directly in Dockerfiles.
Use .dockerignore.
Tag images with meaningful versions.
Keep containers focused on a single responsibility.
Avoid running containers as root when possible.
Regularly update vulnerable dependencies and base images.
Use multi-stage builds for production applications.

Docker Image vs Container

A Docker image is a static template used to create containers.

A Docker container is a running instance of an image.

For example:

docker pull nginx

downloads the Nginx image.

docker run -d -p 8080:80 nginx

creates and starts a container from that image.

The image can be reused to create multiple containers.
