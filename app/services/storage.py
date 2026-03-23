import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings


def save_upload_file(upload: UploadFile) -> Path:
    settings = get_settings()
    suffix = Path(upload.filename or "document").suffix
    filename = f"{uuid4().hex}{suffix}"
    target = settings.upload_dir / filename

    with target.open("wb") as destination:
        shutil.copyfileobj(upload.file, destination)

    return target
