import sys
import urllib.request


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/smoke_task.py <task_id>")

    print(urllib.request.urlopen(f"http://127.0.0.1:8000/api/v1/tasks/{sys.argv[1]}").read().decode())


if __name__ == "__main__":
    main()
