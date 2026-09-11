from langchain_core.tools import tool

from tools.docker_tools import (
    docker_version,
    docker_info,
    list_containers,
    list_images,
    stop_container,
)

from tools.git_tools import (
    git_status,
    git_log,
    git_branch,
    git_remote,
    git_diff,
)

from tools.kubernetes_tools import (
    kubernetes_cluster,
    kubernetes_pods,
    kubernetes_deployments,
    kubernetes_services,
    kubernetes_namespaces,
)


# ==================================================
# DOCKER TOOLS
# ==================================================

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


# ==================================================
# CONTROLLED DOCKER ACTIONS
# ==================================================

@tool
def stop_docker_container(container_name: str) -> str:
    """
    Stop a Docker container.

    This is a potentially destructive operation.
    It must only be executed after explicit user approval.
    """

    result = stop_container(
        container_name
    )

    if result["success"]:
        return (
            f"Docker container '{container_name}' "
            "was stopped successfully."
        )

    return (
        f"Unable to stop Docker container "
        f"'{container_name}': {result['error']}"
    )


# ==================================================
# GIT TOOLS
# ==================================================

@tool
def get_git_status() -> str:
    """Show the current Git branch and working tree status."""

    result = git_status()

    if result["success"]:
        return result["output"]

    return f"Git status failed: {result['error']}"


@tool
def get_git_log() -> str:
    """Show the last 10 Git commits."""

    result = git_log()

    if result["success"]:
        return result["output"]

    return f"Git log failed: {result['error']}"


@tool
def get_git_branch() -> str:
    """Show the current Git branch."""

    result = git_branch()

    if result["success"]:
        return result["output"]

    return f"Git branch check failed: {result['error']}"


@tool
def get_git_remote() -> str:
    """Show configured Git remote repositories."""

    result = git_remote()

    if result["success"]:
        return result["output"]

    return f"Git remote check failed: {result['error']}"


@tool
def get_git_diff() -> str:
    """Show a summary of current Git changes."""

    result = git_diff()

    if result["success"]:
        return result["output"]

    return f"Git diff failed: {result['error']}"


# ==================================================
# KUBERNETES TOOLS
# ==================================================

@tool
def check_kubernetes_cluster() -> str:
    """Check whether a Kubernetes cluster is available."""

    result = kubernetes_cluster()

    if result["success"]:
        return result["output"]

    return (
        "Kubernetes cluster is not available: "
        f"{result['error']}"
    )


@tool
def get_kubernetes_pods() -> str:
    """List Kubernetes pods across all namespaces."""

    result = kubernetes_pods()

    if result["success"]:
        return result["output"]

    return f"Unable to list Kubernetes pods: {result['error']}"


@tool
def get_kubernetes_deployments() -> str:
    """List Kubernetes deployments across all namespaces."""

    result = kubernetes_deployments()

    if result["success"]:
        return result["output"]

    return (
        "Unable to list Kubernetes deployments: "
        f"{result['error']}"
    )


@tool
def get_kubernetes_services() -> str:
    """List Kubernetes services across all namespaces."""

    result = kubernetes_services()

    if result["success"]:
        return result["output"]

    return (
        "Unable to list Kubernetes services: "
        f"{result['error']}"
    )


@tool
def get_kubernetes_namespaces() -> str:
    """List Kubernetes namespaces."""

    result = kubernetes_namespaces()

    if result["success"]:
        return result["output"]

    return (
        "Unable to list Kubernetes namespaces: "
        f"{result['error']}"
    )


# ==================================================
# ALL DEVOPS TOOLS
# ==================================================

DEVOPS_TOOLS = [

    # Docker - read only
    check_docker_version,
    check_docker_status,
    get_docker_containers,
    get_docker_images,

    # Docker - controlled action
    stop_docker_container,

    # Git - read only
    get_git_status,
    get_git_log,
    get_git_branch,
    get_git_remote,
    get_git_diff,

    # Kubernetes - read only
    check_kubernetes_cluster,
    get_kubernetes_pods,
    get_kubernetes_deployments,
    get_kubernetes_services,
    get_kubernetes_namespaces,
]


# ==================================================
# DOCKER TOOLS ONLY
# ==================================================

DOCKER_TOOLS = [

    check_docker_version,
    check_docker_status,
    get_docker_containers,
    get_docker_images,
    stop_docker_container,

]