from mcp.server.fastmcp import FastMCP
import os
import subprocess

mcp= FastMCP("terminal_server")
DEFAULT_WORKSPACE= os.path.expanduser("~/mcp/workspace")

@mcp.tool("terminal_server")
async def run_command(command:str)->str:
    """
    run a command in the terminal and return the output

    Args:
        command(str): the command to run in the terminal

    Returns:
        str:the output of the command or an error message is the command fails.
    """
    try:
        result= subprocess.run(command,shell=True,cwd=DEFAULT_WORKSPACE,text=True,capture_output=True)
        return result.stdout or result.stderr
    except Exception as e:
        return f"Error running command:{str(e)}"
    
if __name__ == "__main__":
    mcp.run(transport="stdio")
    