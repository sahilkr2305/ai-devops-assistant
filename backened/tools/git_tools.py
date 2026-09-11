import subprocess


def run_git_command(command):
    """
    Run a safe read-only Git command.
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
            "error": "Git command timed out.",
            "return_code": -1
        }

    except Exception as e:

        return {
            "success": False,
            "output": "",
            "error": str(e),
            "return_code": -1
        }


def git_status():

    return run_git_command(
        "git status --short --branch"
    )


def git_log():

    return run_git_command(
        "git log --oneline -10"
    )


def git_branch():

    return run_git_command(
        "git branch --show-current"
    )


def git_remote():

    return run_git_command(
        "git remote -v"
    )


def git_diff():

    return run_git_command(
        "git diff --stat"
    )