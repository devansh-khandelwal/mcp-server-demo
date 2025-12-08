from starlette.applications import Starlette
from starlette. routing import Mount
import uvicorn
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("FileReader")

ALLOWED_DIRECTORY = Path("/home/devkhajd/mcp_server_demo/demo3/files/ieee/ieee_txt_files/"). resolve()


def is_path_allowed(file_path: str) -> tuple[bool, str]:
    """
    Check if the given path is within the allowed directory.
    
    Returns:
        tuple: (is_allowed: bool, error_message: str)
    """
    try:
        path = Path(file_path). resolve()
        
        if not path.is_relative_to(ALLOWED_DIRECTORY):
            return False, f"Error: Access denied.  Only files within '{ALLOWED_DIRECTORY}' are allowed."
        
        return True, ""
    except Exception as e:
        return False, f"Error: Invalid path - {str(e)}"


@mcp.tool()
async def read_file_tool(file_path: str) -> str:
    """
    Read the contents of a file from the allowed directory.
    If only a filename is provided, it will look in the allowed directory.
    
    Args:
        file_path (str): The path to the file to read (can be absolute or just filename).
    
    Returns:
        str: The contents of the file or an error message.
    """
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = ALLOWED_DIRECTORY / file_path
        
        path = path.resolve()
        
        is_allowed, error_msg = is_path_allowed(str(path))
        if not is_allowed:
            return error_msg
        
        if not path.exists():
            return f"Error: File '{path. name}' does not exist in the allowed directory."
        
        if not path.is_file():
            return f"Error: '{path.name}' is not a file."
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return f"File: {path.name}\nPath: {path}\n\nContent:\n{content}"
    
    except PermissionError:
        return f"Error: Permission denied reading '{file_path}'."
    except UnicodeDecodeError:
        return f"Error: Unable to decode '{file_path}' as text.  It may be a binary file."
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
async def list_files_in_directory_tool(subdirectory: str = "", pattern: str = "*") -> str:
    """
    List all files in the allowed directory or a subdirectory within it.
    
    Args:
        subdirectory (str): Optional subdirectory within the allowed directory (e.g., "subdir1/subdir2").
        pattern (str): Optional glob pattern to filter files (e.g., "*.txt", "*.py"). Defaults to "*" (all files).
    
    Returns:
        str: A list of files in the directory or an error message.
    """
    try:
        
        if subdirectory:
            target_dir = (ALLOWED_DIRECTORY / subdirectory).resolve()
        else:
            target_dir = ALLOWED_DIRECTORY
        
        is_allowed, error_msg = is_path_allowed(str(target_dir))
        if not is_allowed:
            return error_msg
        
        if not target_dir.exists():
            return f"Error: Subdirectory '{subdirectory}' does not exist in the allowed directory."
        
        if not target_dir.is_dir():
            return f"Error: '{subdirectory}' is not a directory."
        
        files = [f for f in target_dir. glob(pattern) if f.is_file()]
        
        if not files:
            return f"No files found matching pattern '{pattern}' in the specified directory."
        
        file_list = "\n".join([f"  - {f.name} ({f.stat().st_size} bytes)" for f in sorted(files)])
        return f"Files in '{target_dir. relative_to(ALLOWED_DIRECTORY. parent)}' matching '{pattern}':\n{file_list}\n\nTotal: {len(files)} file(s)"
    
    except PermissionError:
        return f"Error: Permission denied accessing the directory."
    except Exception as e:
        return f"Error listing files: {str(e)}"


@mcp.tool()
async def read_multiple_files_tool(subdirectory: str = "", pattern: str = "*") -> str:
    """
    Read contents of all files in the allowed directory (or subdirectory) matching a pattern.
    
    Args:
        subdirectory (str): Optional subdirectory within the allowed directory. 
        pattern (str): Optional glob pattern to filter files (e.g., "*.txt", "*.py"). Defaults to "*" (all files).
    
    Returns:
        str: Contents of all matching files or an error message.
    """
    try:
       
        if subdirectory:
            target_dir = (ALLOWED_DIRECTORY / subdirectory).resolve()
        else:
            target_dir = ALLOWED_DIRECTORY
        
        is_allowed, error_msg = is_path_allowed(str(target_dir))
        if not is_allowed:
            return error_msg
        
        if not target_dir.exists():
            return f"Error: Subdirectory '{subdirectory}' does not exist in the allowed directory."
        
        if not target_dir.is_dir():
            return f"Error: '{subdirectory}' is not a directory."
        
        files = [f for f in target_dir.glob(pattern) if f.is_file()]
        
        if not files:
            return f"No files found matching pattern '{pattern}' in the specified directory."
        
        results = [f"Reading {len(files)} file(s) from '{target_dir.relative_to(ALLOWED_DIRECTORY. parent)}':\n"]
        
        for file in sorted(files):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                results.append(f"\n{'='*60}\nFile: {file.name}\n{'='*60}\n{content}\n")
            except UnicodeDecodeError:
                results.append(f"\n{'='*60}\nFile: {file.name}\n{'='*60}\n[Binary file - cannot display as text]\n")
            except Exception as e:
                results.append(f"\n{'='*60}\nFile: {file.name}\n{'='*60}\nError: {str(e)}\n")
        
        return "".join(results)
    
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def search_file_content_tool(search_term: str, pattern: str = "*.txt") -> str:
    """
    Search for a term within all files in the allowed directory. 
    
    Args:
        search_term (str): The text to search for within files.
        pattern (str): File pattern to search within (e.g., "*.txt").  Defaults to "*.txt". 
    
    Returns:
        str: Files containing the search term with matching lines.
    """
    try:
        files = [f for f in ALLOWED_DIRECTORY.rglob(pattern) if f. is_file()]
        
        if not files:
            return f"No files found matching pattern '{pattern}'."
        
        results = []
        matches_found = 0
        
        for file in sorted(files):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                matching_lines = []
                for line_num, line in enumerate(lines, 1):
                    if search_term. lower() in line.lower():
                        matching_lines.append(f"  Line {line_num}: {line. rstrip()}")
                
                if matching_lines:
                    matches_found += 1
                    results.append(f"\n {file.name}:\n" + "\n".join(matching_lines))
            
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
        
        if not results:
            return f"No matches found for '{search_term}' in files matching '{pattern}'."
        
        return f"Found '{search_term}' in {matches_found} file(s):\n" + "\n".join(results)
    
    except Exception as e:
        return f"Error searching files: {str(e)}"


app = Starlette(
    routes=[
        Mount('/', app=mcp.sse_app()),
    ]
)

if __name__ == "__main__":
    print("Starting File Reader MCP Server....")
    print(f"Allowed directory: {ALLOWED_DIRECTORY}")
    print("\nAvailable tools:")
    print("  - read_file_tool: Read a single file")
    print("  - list_files_in_directory_tool: List files in directory")
    print("  - read_multiple_files_tool: Read all matching files")
    print("  - search_file_content_tool: Search for text within files")
    print(f"\nServer running at http://localhost:8000")
    uvicorn.run(app, host="localhost", port=8000)