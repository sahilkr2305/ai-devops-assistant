import re
import subprocess


# Only allow simple Docker container names/IDs.
# This prevents shell flags and special characters from
# being passed as arguments.
CONTAINER_NAME_PATTERN = re.compile(
    r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$"
)


def run_command(command: list[str]):
    """
    Safely execute an allowlisted command without a shell.

    shell=False prevents shell injection such as:
    ; whoami
    && del ...
    | malicious_command
    """

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15,
            shell=False
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
            "error": result.stderr.strip(),
            "return_code": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Command timed out.",
            "return_code": -1
        }

    except FileNotFoundError:
        return {
            "success": False,
            "output": "",
            "error": f"Command not found: {command[0]}",
            "return_code": -1
        }

    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "return_code": -1
        }


def docker_version():
    return run_command([
        "docker",
        "--version"
    ])


def docker_info():
    return run_command([
        "docker",
        "info"
    ])


def list_containers():
    return run_command([
        "docker",
        "ps",
        "-a"
    ])


def list_images():
    return run_command([
        "docker",
        "images"
    ])


def stop_container(container_name: str):
    """
    Stop a Docker container.

    This is a potentially destructive operation
    and must only be called after approval.
    """

    if not isinstance(container_name, str):
        return {
            "success": False,
            "output": "",
            "error": "Invalid container name.",
            "return_code": -1
        }

    container_name = container_name.strip()

    if not container_name:
        return {
            "success": False,
            "output": "",
            "error": "Container name cannot be empty.",
            "return_code": -1
        }

    if not CONTAINER_NAME_PATTERN.fullmatch(container_name):
        return {
            "success": False,
            "output": "",
            "error": (
                "Invalid container name. Only letters, numbers, "
                "dots, underscores, and hyphens are allowed."
            ),
            "return_code": -1
        }

    return run_command([
        "docker",
        "stop",
        container_name
    ])