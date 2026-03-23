import json
import sys
import urllib.request


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/smoke_index.py <document_id>")

    payload = json.dumps({"document_id": sys.argv[1], "metadata": {}}).encode()
    request = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/documents/index",
        data=payload,
        method="POST",
    )
    request.add_header("Content-Type", "application/json")
    print(urllib.request.urlopen(request).read().decode())


if __name__ == "__main__":
    main()
