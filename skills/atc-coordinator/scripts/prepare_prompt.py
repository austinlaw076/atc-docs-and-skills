#!/usr/bin/env python3
"""Render complete source and schema without altering request fields."""
import argparse
import json
import sys
from pathlib import Path

RUNTIME = Path(__file__).resolve().parent / "runtime"
sys.path.insert(0, str(RUNTIME))


def main():
    from atc10.core import digest
    from atc10.runtime import delivery_payload

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    args = parser.parse_args()
    try:
        if args.request.stat().st_size > 2_000_000:
            raise ValueError("request exceeds 2 MB budget")
        envelope = json.loads(args.request.read_text(encoding="utf-8"))
        if not isinstance(envelope, dict) or envelope.get("role") not in ("worker", "reviewer"):
            raise ValueError("unknown request role")
        if envelope.get("input_hash") != digest({k: v for k, v in envelope.items() if k != "input_hash"}):
            raise ValueError("request input_hash mismatch")
        sys.stdout.write(delivery_payload(envelope)['prompt'])
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
