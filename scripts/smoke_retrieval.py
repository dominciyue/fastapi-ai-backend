import json
import sys
import urllib.request


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "How do I use this service?"
    payload = json.dumps({"query": query, "top_k": 3}).encode()
    request = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/retrieval/search",
        data=payload,
        method="POST",
    )
    request.add_header("Content-Type", "application/json")
    print(urllib.request.urlopen(request).read().decode())


if __name__ == "__main__":
    main()
