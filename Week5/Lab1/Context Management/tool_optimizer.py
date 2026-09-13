"""Shrink bulky tool outputs to a per-tool whitelist before they hit the model."""

# Fields we actually care about for each tool. Anything not in this list
# is dropped before the result reaches the model.
RELEVANT_FIELDS = {
    "lookup_orders":     ["order_id", "status", "placed_on", "total"],
    "get_order_details": ["order_id", "status", "placed_on", "total", "items"],
}


def optimize(tool_name: str, raw_result):
    """
    Trim a tool's raw output down to just the fields that matter.

    Returns the trimmed result in the same shape (list or dict) it came in.
    Unknown tools pass through untouched (consider logging a warning in
    production so unconfigured tools don't sneak past).
    """
    keep = RELEVANT_FIELDS.get(tool_name)
    if keep is None:
        return raw_result

    if isinstance(raw_result, list):
        return [{k: row[k] for k in keep if k in row} for row in raw_result]

    if isinstance(raw_result, dict):
        return {k: raw_result[k] for k in keep if k in raw_result}

    return raw_result
