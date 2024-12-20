import shutil
from pathlib import Path
from typing import List

from fastapi import UploadFile

from ragbase.config import Config


def upload_files(
    files: List[UploadFile], remove_old_files: bool = True
) -> List[Path]:
    if remove_old_files:
        shutil.rmtree(Config.Path.DATABASE_DIR, ignore_errors=True)
        shutil.rmtree(Config.Path.DOCUMENTS_DIR, ignore_errors=True)
    Config.Path.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    file_paths = []
    for file in files:
        file_path = Config.Path.DOCUMENTS_DIR / file.filename
        with file_path.open("wb") as f:
            # Use file.read() for FastAPI UploadFile
            f.write(file.file.read())
        file.file.close()  # Close the file explicitly
        file_paths.append(file_path)
    return file_paths
