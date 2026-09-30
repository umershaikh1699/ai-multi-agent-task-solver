from __future__ import annotations
from typing import Any, Dict, List

class Pick:
    name = "json.pick"

    def __init__(self) -> None:
        ...

    def _get_path(self, data: Any, path: str) -> Any:
        # Handle list projection if data is a list and path doesn't start with index
        if isinstance(data, list) and path and not path.strip().startswith("["):
             # If data is a list and we ask for "key", we probably want [item["key"] for item in data]
             # This is a simple projection
             results = []
             for item in data:
                 if isinstance(item, dict):
                     val = item.get(path)
                     results.append(val)
             return results

        cur = data
        parts = path.split(".") if path else []
        for part in parts:
            if cur is None: 
                return None
                
            if "[" in part and part.endswith("]"):
                key, idx_str = part[:-1].split("[")
                if key:
                    if isinstance(cur, dict):
                        cur = cur.get(key)
                    else:
                        return None
                
                try:
                    idx = int(idx_str)
                    if isinstance(cur, list) and 0 <= idx < len(cur):
                         cur = cur[idx]
                    else:
                         return None
                except ValueError:
                    return None
            else:
                if isinstance(cur, list):
                    # Trying to access property on a list -> try projection
                    try:
                        idx = int(part)
                        if 0 <= idx < len(cur):
                            cur = cur[idx]
                        else:
                            return None
                    except ValueError:
                        # Fallback: if we are at a list and request a key, project it?
                        # But we are inside a path traversal.
                        # For simplicity, if we hit a list in the middle of a path, mapping is hard without full JMESPath.
                        # Let's just return None to be safe, or implement simple projection if it's the last part.
                        return None
                elif isinstance(cur, dict):
                    if part in cur:
                        cur = cur.get(part)
                    # Smart Fallback: Agent often forgets that http.get returns wrapper {json: ...}
                    # If we look for 'quotes' but only find 'json', look inside 'json'.
                    elif "json" in cur and isinstance(cur["json"], dict) and part in cur["json"]:
                        cur = cur["json"][part]
                    elif "data" in cur and isinstance(cur["data"], dict) and part in cur["data"]:
                        cur = cur["data"][part]
                    else:
                        return None
                else:
                    return None
        return cur

    async def run(self, data: Any, paths: List[str]) -> Dict[str, Any]:
        out = {}
        for p in paths:
            out[p] = self._get_path(data, p)
        return {"picked": out}
