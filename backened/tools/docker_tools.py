import subprocess


def run_command(command):
    """
    Run a safe read-only Docker command
    and return its output.
    """

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15,
            shell=True
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

    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "return_code": -1
        }


def docker_version():
    """
    Check Docker version.
    """

    return run_command(
        "docker --version"
    )


def docker_info():
    """
    Check whether Docker Engine is running.
    """

    return run_command(
        "docker info"
    )


def list_containers():
    """
    List Docker containers.
    """

    return run_command(
        "docker ps -a"
    )


def list_images():
    """
    List Docker images.
    """

    return run_command(
        "docker images"
    )
