from starlette.applications import Starlette
from starlette. routing import Mount
import uvicorn
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("FileReader")

RESOURCE_DIR = (Path(__file__).parent / "ieee_txt_files").resolve()
RESOURCES: dict[str, dict] = {}

def _load_resources() -> None:
    try:
        if RESOURCE_DIR.exists() and RESOURCE_DIR.is_dir():
            for f in sorted(RESOURCE_DIR.glob("*")):
                if f.is_file():
                    try:
                        content = f.read_text(encoding="utf-8")
                        RESOURCES[f.name] = {
                            "name": f.name,
                            "path": str(f),
                            "size": f.stat().st_size,
                            "content": content,
                        }
                    except UnicodeDecodeError:
                        continue
        else:
            pass
    except Exception:
        pass

_load_resources()


def _get_resource(name: str) -> tuple[bool, str | dict]:
    if name in RESOURCES:
        return True, RESOURCES[name]
    else:
        return False, f"Error: Resource '{name}' not found."


@mcp.tool()
async def read_file_tool(file_path: str) -> str:
    """
    Read the contents of an in-memory resource loaded by the MCP server.
    
    Args:
        file_path (str): Resource name (filename) to read.
    
    Returns:
        str: The contents of the file or an error message.
    """
    try:
        ok, res = _get_resource(Path(file_path).name)
        if not ok:
            return str(res)
        resource = res 
        return f"File: {resource['name']}\nPath: {resource['path']}\n\nContent:\n{resource['content']}"
    except Exception as e:
        return f"Error reading resource: {str(e)}"


@mcp.tool()
async def list_files_in_directory_tool(pattern: str = "*") -> str:
    """
    List all in-memory resources (optionally filtered by a glob pattern).
    
    Args:
        pattern (str): Optional glob pattern to filter resources (e.g., "*.txt"). Defaults to "*".
    
    Returns:
        str: A list of files in the directory or an error message.
    """
    try:
        from fnmatch import fnmatch
        matching = [r for r in RESOURCES.values() if fnmatch(r["name"], pattern)]
        if not matching:
            return f"No resources found matching pattern '{pattern}'."
        file_list = "\n".join([f"  - {r['name']} ({r['size']} bytes)" for r in sorted(matching, key=lambda x: x["name"])])
        return f"Resources matching '{pattern}':\n{file_list}\n\nTotal: {len(matching)} resource(s)"
    except Exception as e:
        return f"Error listing resources: {str(e)}"


@mcp.tool()
async def read_multiple_files_tool(pattern: str = "*") -> str:
    """
    Read contents of all in-memory resources matching a pattern.
    
    Args:
        subdirectory (str): Ignored for in-memory resources.
        pattern (str): Optional glob pattern to filter resources (e.g., "*.txt"). Defaults to "*".
    
    Returns:
        str: Contents of all matching files or an error message.
    """
    try:
        from fnmatch import fnmatch
        matching = [r for r in RESOURCES.values() if fnmatch(r["name"], pattern)]
        if not matching:
            return f"No resources found matching pattern '{pattern}'."
        results = [f"Reading {len(matching)} resource(s) matching '{pattern}':\n"]
        for r in sorted(matching, key=lambda x: x["name"]):
            results.append(f"\n{'='*60}\nFile: {r['name']}\n{'='*60}\n{r['content']}\n")
        return "".join(results)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def search_file_content_tool(search_term: str, pattern: str = "*.txt") -> str:
    """
    Search for a term within all in-memory resources.
    
    Args:
        search_term (str): The text to search for within files.
        pattern (str): Resource pattern to search within (e.g., "*.txt"). Defaults to "*.txt". 
    
    Returns:
        str: Files containing the search term with matching lines.
    """
    try:
        from fnmatch import fnmatch
        matching = [r for r in RESOURCES.values() if fnmatch(r["name"], pattern)]
        if not matching:
            return f"No resources found matching pattern '{pattern}'."
        results = []
        matches_found = 0
        for r in sorted(matching, key=lambda x: x["name"]):
            lines = r["content"].splitlines()
            matching_lines = []
            for line_num, line in enumerate(lines, 1):
                if search_term.lower() in line.lower():
                    matching_lines.append(f"  Line {line_num}: {line.rstrip()}")
            if matching_lines:
                matches_found += 1
                results.append(f"\n {r['name']}:\n" + "\n".join(matching_lines))
        if not results:
            return f"No matches found for '{search_term}' in resources matching '{pattern}'."
        return f"Found '{search_term}' in {matches_found} resource(s):\n" + "\n".join(results)
    except Exception as e:
        return f"Error searching resources: {str(e)}"


app = Starlette(
    routes=[
        Mount('/', app=mcp.sse_app()),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)