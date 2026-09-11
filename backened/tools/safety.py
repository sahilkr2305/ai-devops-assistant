# ==================================================
# DEVOPS SAFETY LAYER
# ==================================================

# Actions that require explicit user approval.
DANGEROUS_ACTIONS = {
    "stop_docker_container",

    "docker_stop",
    "docker_rm",
    "docker_rmi",

    "git_reset",
    "git_push",
    "git_clean",

    "kubectl_delete",
    "kubectl_apply",
}

def is_dangerous_action(action_name: str) -> bool:
    """
    Return True when an action requires approval.
    """

    return action_name in DANGEROUS_ACTIONS


def approval_message(action_name: str) -> str:
    """
    Create a warning shown to the user.
    """

    return (
        "⚠️ Approval required\n\n"
        f"Action: `{action_name}`\n\n"
        "This operation can modify or delete resources. "
        "Explicit user approval is required before execution."
    )


def can_execute(
    action_name: str,
    approval_status: str | None = None
) -> bool:
    """
    Determine whether an action is allowed to execute.

    Read-only actions can execute immediately.

    Dangerous actions require:
        approval_status == 'approved'
    """

    if not is_dangerous_action(action_name):
        return True

    return approval_status == "approved"