from mcp.server.fastmcp import FastMCP
import logging
import os
import shlex
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("terminal_server")
DEFAULT_WORKSPACE = os.path.expanduser("~/mcp/workspace")

# Commands that are allowed to run (whitelist for safety)
ALLOWED_COMMANDS = {
    "ls", "cat", "head", "tail", "grep", "find", "wc", "echo", "pwd", "date",
    "mkdir", "touch", "cp", "mv", "rm", "tree", "file", "stat", "du", "df",
    "python", "python3", "node", "npm", "pip", "uv", "git",
}


def validate_command(args: list[str]) -> tuple[bool, str]:
    """
    Validate that the command is safe to execute.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not args:
        return False, "Empty command"
    
    base_cmd = os.path.basename(args[0])
    
    if base_cmd not in ALLOWED_COMMANDS:
        return False, f"Command '{base_cmd}' is not in the allowed list. Allowed: {', '.join(sorted(ALLOWED_COMMANDS))}"
    
    # Check for shell metacharacters that could be dangerous
    dangerous_chars = [";", "&&", "||", "|", "`", "$", "(", ")", "{", "}", "<", ">", "\\"]
    full_command = " ".join(args)
    for char in dangerous_chars:
        if char in full_command:
            return False, f"Command contains disallowed character: '{char}'"
    
    return True, ""


@mcp.tool("terminal_server")
async def run_command(command: str) -> str:
    """
    Run a command in the terminal and return the output.
    
    Only whitelisted commands are allowed for security.
    Shell metacharacters are blocked to prevent injection.

    Args:
        command: The command to run in the terminal

    Returns:
        The output of the command or an error message if the command fails.
    """
    # Ensure workspace exists
    os.makedirs(DEFAULT_WORKSPACE, exist_ok=True)
    
    try:
        # Parse command safely without shell interpretation
        args = shlex.split(command)
    except ValueError as e:
        logger.warning(f"Failed to parse command: {command!r} - {e}")
        return f"Error: Invalid command format - {e}"
    
    # Validate the command
    is_valid, error_msg = validate_command(args)
    if not is_valid:
        logger.warning(f"Command rejected: {command!r} - {error_msg}")
        return f"Error: {error_msg}"
    
    try:
        logger.info(f"Executing command: {args}")
        result = subprocess.run(
            args,
            shell=False,  # SECURITY: Never use shell=True with user input
            cwd=DEFAULT_WORKSPACE,
            text=True,
            capture_output=True,
            timeout=30,  # Prevent runaway commands
        )
        
        output = result.stdout or result.stderr or "(no output)"
        if result.returncode != 0:
            output = f"[Exit code: {result.returncode}]\n{output}"
        
        return output
        
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {args}")
        return "Error: Command timed out after 30 seconds"
    except FileNotFoundError:
        logger.error(f"Command not found: {args[0]}")
        return f"Error: Command not found: {args[0]}"
    except PermissionError as e:
        logger.error(f"Permission denied: {args} - {e}")
        return f"Error: Permission denied - {e}"
    except OSError as e:
        logger.error(f"OS error running command: {args} - {e}")
        return f"Error running command: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
    