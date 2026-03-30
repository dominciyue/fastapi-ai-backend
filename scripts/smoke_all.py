import argparse
import json
import pathlib
import time
import urllib.request

BOUNDARY = "----SmokeAllBoundary7MA4YWxkTrZu0gW"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_QUERY = "What does the uploaded file describe?"


def request_json(url: str, *, data: bytes | None = None, content_type: str | None = None) -> dict:
    request = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
    if content_type:
        request.add_header("Content-Type", content_type)

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def request_stream(url: str, payload: dict) -> list[str]:
    data = json.dumps(payload).encode()
    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("Content-Type", "application/json")

    lines: list[str] = []
    with urllib.request.urlopen(request) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="ignore").strip()
            if line:
                lines.append(line)
    return lines


def upload_document(base_url: str, file_path: pathlib.Path) -> dict:
    body = (
        (
            f"--{BOUNDARY}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            "Content-Type: text/markdown\r\n\r\n"
        ).encode()
        + file_path.read_bytes()
        + f"\r\n--{BOUNDARY}--\r\n".encode()
    )
    request = urllib.request.Request(
        f"{base_url}/api/v1/documents/upload",
        data=body,
        method="POST",
    )
    request.add_header("Content-Type", f"multipart/form-data; boundary={BOUNDARY}")

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def wait_for_task(
    base_url: str, task_id: str, timeout_seconds: int, interval_seconds: float
) -> dict:
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        task = request_json(f"{base_url}/api/v1/tasks/{task_id}")
        status = task["status"]
        if status == "completed":
            return task
        if status == "failed":
            raise RuntimeError(f"Indexing task failed: {task.get('detail') or 'unknown error'}")
        time.sleep(interval_seconds)

    raise TimeoutError(f"Timed out waiting for task {task_id} to finish within {timeout_seconds}s")


def ensure_readiness(base_url: str) -> dict:
    readiness = request_json(f"{base_url}/health/ready")
    if readiness.get("status") != "ok":
        raise RuntimeError(f"Service is not ready: {json.dumps(readiness, ensure_ascii=False)}")
    return readiness


def ensure_stream_events(lines: list[str]) -> None:
    required_events = {"event: sources", "event: token", "event: done"}
    missing = [event for event in required_events if event not in lines]
    if missing:
        raise RuntimeError(f"Missing expected stream events: {', '.join(missing)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full smoke flow against the local API.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--file", default="tests/fixtures/sample.md")
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--interval", type=float, default=2.0)
    args = parser.parse_args()

    file_path = pathlib.Path(args.file)
    if not file_path.exists():
        raise SystemExit(f"File not found: {file_path}")

    print("[1/6] Checking readiness...")
    readiness = ensure_readiness(args.base_url)
    print(json.dumps(readiness, ensure_ascii=False))

    print("[2/6] Uploading document...")
    upload_payload = upload_document(args.base_url, file_path)
    document_id = upload_payload["document"]["id"]
    print(json.dumps(upload_payload, ensure_ascii=False))

    print("[3/6] Creating indexing task...")
    index_payload = request_json(
        f"{args.base_url}/api/v1/documents/index",
        data=json.dumps({"document_id": document_id, "metadata": {}}).encode(),
        content_type="application/json",
    )
    task_id = index_payload["id"]
    print(json.dumps(index_payload, ensure_ascii=False))

    print("[4/6] Waiting for indexing task...")
    task_payload = wait_for_task(args.base_url, task_id, args.timeout, args.interval)
    print(json.dumps(task_payload, ensure_ascii=False))

    print("[5/6] Running retrieval and sync query...")
    retrieval_payload = request_json(
        f"{args.base_url}/api/v1/retrieval/search",
        data=json.dumps({"query": args.query, "top_k": 3}).encode(),
        content_type="application/json",
    )
    query_payload = request_json(
        f"{args.base_url}/api/v1/chat/query",
        data=json.dumps(
            {"query": args.query, "top_k": 3, "system_prompt": "Answer briefly in Chinese."}
        ).encode(),
        content_type="application/json",
    )
    if not retrieval_payload.get("hits"):
        raise RuntimeError("Retrieval returned no hits.")
    if not query_payload.get("answer"):
        raise RuntimeError("Chat query returned an empty answer.")
    print(json.dumps(retrieval_payload, ensure_ascii=False))
    print(json.dumps(query_payload, ensure_ascii=False))

    print("[6/6] Running stream query...")
    stream_lines = request_stream(
        f"{args.base_url}/api/v1/chat/stream",
        {"query": args.query, "top_k": 3},
    )
    ensure_stream_events(stream_lines)
    print("\n".join(stream_lines))

    print("Smoke flow completed successfully.")


if __name__ == "__main__":
    main()
