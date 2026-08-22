"""NorthPeak Docs - a tiny MCP server (the "docs" source).

Exposes the company policy documents (shipping, returns, warranty) over MCP so
Claude Code can search and read them as a second, independent source.
"""
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("northpeak-docs")
DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "docs"


@mcp.tool()
def list_docs() -> dict:
    """List the names of all available policy documents."""
    return {"docs": sorted(p.stem for p in DOCS_DIR.glob("*.md"))}


@mcp.tool()
def read_doc(name: str) -> dict:
    """Read the full text of one policy document by name (no .md extension)."""
    path = DOCS_DIR / f"{name}.md"
    if not path.exists():
        return {"found": False, "error": f"No doc named '{name}'. Try list_docs."}
    return {"found": True, "name": name, "content": path.read_text()}


@mcp.tool()
def search_docs(query: str) -> dict:
    """Find policy documents whose text contains the query (case-insensitive)."""
    q = query.strip().lower()
    hits = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        text = path.read_text()
        i = text.lower().find(q)
        if i != -1:
            snippet = text[max(0, i - 60):i + 120].replace("\n", " ").strip()
            hits.append({"name": path.stem, "snippet": f"...{snippet}..."})
    return {"count": len(hits), "results": hits}


if __name__ == "__main__":
    mcp.run()