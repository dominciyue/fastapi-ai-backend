import json
import urllib.request


def main() -> None:
    payload = json.dumps({"query": "Summarize the uploaded file.", "top_k": 3}).encode()
    request = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/chat/stream",
        data=payload,
        method="POST",
    )
    request.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(request) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="ignore").strip()
            if line:
                print(line)


if __name__ == "__main__":
    main()
