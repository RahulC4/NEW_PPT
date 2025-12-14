# DEBUG (temporarily keep this)
logger.info("LLM RAW RESPONSE:\n" + raw)

parsed = safe_json_load(raw)

# Case 1: proper dict
if isinstance(parsed, dict) and isinstance(parsed.get("questions"), list):
    return parsed["questions"]

# Case 2: LLM returns list directly
if isinstance(parsed, list):
    return parsed

# Case 3: try manual extraction
try:
    import re
    json_block = re.search(r"\{[\s\S]*\}", raw)
    if json_block:
        parsed = json.loads(json_block.group())
        if isinstance(parsed.get("questions"), list):
            return parsed["questions"]
except Exception:
    pass
