import subprocess


def run_kubectl_command(command: list[str]):
    """
    Safely execute a kubectl command without using a shell.

    shell=False prevents shell injection and ensures each
    argument is passed directly to kubectl.
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
            "error": "kubectl command timed out.",
            "return_code": -1
        }

    except FileNotFoundError:
        return {
            "success": False,
            "output": "",
            "error": "kubectl executable was not found.",
            "return_code": -1
        }

    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e),
            "return_code": -1
        }


def kubernetes_cluster():
    return run_kubectl_command([
        "kubectl",
        "cluster-info"
    ])


def kubernetes_pods():
    return run_kubectl_command([
        "kubectl",
        "get",
        "pods",
        "-A"
    ])


def kubernetes_deployments():
    return run_kubectl_command([
        "kubectl",
        "get",
        "deployments",
        "-A"
    ])


def kubernetes_services():
    return run_kubectl_command([
        "kubectl",
        "get",
        "services",
        "-A"
    ])


def kubernetes_namespaces():
    return run_kubectl_command([
        "kubectl",
        "get",
        "namespaces"
    ])