from langchain_core.tools import tool

from tools.docker_tools import (
    docker_version,
    docker_info,
    list_containers,
    list_images,
)


@tool
def check_docker_version() -> str:
    """Check whether Docker is installed and return its version."""

    result = docker_version()

    if result["success"]:
        return result["output"]

    return f"Docker version check failed: {result['error']}"


@tool
def check_docker_status() -> str:
    """Check whether the Docker Engine is running."""

    result = docker_info()

    if result["success"]:
        return result["output"]

    return f"Docker status check failed: {result['error']}"


@tool
def get_docker_containers() -> str:
    """List all Docker containers, including stopped containers."""

    result = list_containers()

    if result["success"]:
        return result["output"]

    return f"Unable to list Docker containers: {result['error']}"


@tool
def get_docker_images() -> str:
    """List Docker images available locally."""

    result = list_images()

    if result["success"]:
        return result["output"]

    return f"Unable to list Docker images: {result['error']}"


DOCKER_TOOLS = [
    check_docker_version,
    check_docker_status,
    get_docker_containers,
    get_docker_images,
]
