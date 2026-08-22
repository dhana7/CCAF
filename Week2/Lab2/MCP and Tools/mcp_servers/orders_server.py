"""NorthPeak Orders - a tiny MCP server (the "database" source).

Exposes two tools over MCP so Claude Code can look up order data without you
pasting anything into the chat. Claude Code launches this script via .mcp.json.
"""
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("northpeak-orders")
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "orders.json"
ORDERS = json.loads(DATA_FILE.read_text())


@mcp.tool()
def get_order(order_id: str) -> dict:
    """Look up a single order by its ID (format 'NP-XXXXXX')."""
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"found": False, "error": f"No order with id '{order_id}'."}
    return {"found": True, **order}


@mcp.tool()
def find_orders_by_email(email: str) -> dict:
    """Find all orders placed by a customer email address."""
    matches = [{"order_id": oid, **o} for oid, o in ORDERS.items()
               if o.get("email", "").lower() == email.strip().lower()]
    return {"count": len(matches), "orders": matches}


if __name__ == "__main__":
    mcp.run()  # stdio transport - this is what Claude Code connects to