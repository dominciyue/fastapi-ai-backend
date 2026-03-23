from pathlib import Path

from app.services.document_parser import parse_document


def test_parse_plain_text_file(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello world", encoding="utf-8")
    assert parse_document(file_path) == "hello world"
