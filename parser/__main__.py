from __future__ import annotations
import argparse, json
from pathlib import Path
from .core import parse_brief, usage_stats

def main() -> None:
    p = argparse.ArgumentParser(description="Parse an unstructured hiring brief")
    p.add_argument("--input", required=True); p.add_argument("--out", required=True)
    args = p.parse_args(); result = parse_brief(Path(args.input).read_text(encoding="utf-8"))
    target = Path(args.out); target.parent.mkdir(parents=True, exist_ok=True); target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(target), "token_usage": usage_stats()}))
if __name__ == "__main__": main()
