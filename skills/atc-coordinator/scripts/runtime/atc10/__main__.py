"""JSON-only host bridge CLI. No shell commands or arbitrary worker code."""
import argparse
import json
import sys
from pathlib import Path

from .core import ContractError, Coordinator, compile_prd


def main():
    parser = argparse.ArgumentParser(description="ATC 1.1 trusted host bridge")
    parser.add_argument("--prd", default="examples/atc10/prd.json")
    parser.add_argument("--run", default="outputs/atc10-live")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("compile")
    sub.add_parser("report")
    dispatch = sub.add_parser("dispatch")
    dispatch.add_argument("task")
    dispatch.add_argument("--role", choices=("worker", "reviewer"), default="worker")
    dispatch.add_argument("--ttl", type=int, default=900)
    prompt = sub.add_parser("prompt")
    prompt.add_argument("request")
    delivered = sub.add_parser("delivered")
    delivered.add_argument("request")
    delivered.add_argument("agent")
    delivered.add_argument("prompt_sha256")
    delivered.add_argument("receipt_id")
    bind = sub.add_parser("bind")
    bind.add_argument("request")
    bind.add_argument("agent")
    receive = sub.add_parser("receive")
    receive.add_argument("request")
    receive.add_argument("agent")
    receive.add_argument("response", help="JSON response file from trusted host")
    fail = sub.add_parser("fail")
    fail.add_argument("request")
    fail.add_argument("reason")
    args = parser.parse_args()
    coord = None
    try:
        path = Path(args.prd)
        bundle = compile_prd(json.loads(path.read_text()), path.parent)
        if args.command == "compile":
            result = bundle
        else:
            coord = Coordinator(bundle, args.run)
            if args.command == "report":
                result = coord.report()
            elif args.command == "dispatch":
                result = coord.dispatch(args.task, args.role, args.ttl)
            elif args.command == "prompt":
                print(coord.delivery(args.request)['prompt'], end='')
                return 0
            elif args.command == "delivered":
                coord.record_delivery(args.request, args.agent, args.prompt_sha256, args.receipt_id)
                result = {"delivery_recorded": True}
            elif args.command == "bind":
                coord.bind(args.request, args.agent)
                result = {"bound": True}
            elif args.command == "receive":
                response_path = Path(args.response)
                if response_path.stat().st_size > 500_000:
                    raise ContractError("response file exceeds 500 KB")
                result = {"status": coord.receive(args.request, args.agent,
                                                  json.loads(response_path.read_text()))}
            else:
                coord.fail(args.request, args.reason)
                result = {"failure_recorded": True}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ContractError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    finally:
        if coord:
            coord.close()


if __name__ == "__main__":
    raise SystemExit(main())
