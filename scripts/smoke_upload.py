import pathlib
import urllib.request

BOUNDARY = "----WebKitFormBoundary7MA4YWxkTrZu0gW"


def main() -> None:
    path = pathlib.Path("tests/fixtures/sample.md")
    data = path.read_bytes()
    body = (
        (
            f"--{BOUNDARY}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
            "Content-Type: text/markdown\r\n\r\n"
        ).encode()
        + data
        + f"\r\n--{BOUNDARY}--\r\n".encode()
    )
    request = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/documents/upload",
        data=body,
        method="POST",
    )
    request.add_header("Content-Type", f"multipart/form-data; boundary={BOUNDARY}")
    print(urllib.request.urlopen(request).read().decode())


if __name__ == "__main__":
    main()
