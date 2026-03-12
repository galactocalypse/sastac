import hashlib
from pathlib import Path
from sastac.ast.models.file_meta import FileMetadata


def extract_language(filename):
    ext = filename.split(".")[-1]
    if ext == "js":
        return "javascript"
    if ext in {"ts", "tsx"}:
        return "typescript"
    if ext == "py":
        return "python"
    return ext

def compute_file_hash(file_path, algorithm='sha256', buffer_size=65536):
    """Computes the hash of a file by reading it in chunks."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        while chunk := f.read(buffer_size):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def get_file_meta(file_path):
    name = Path(file_path).name

    language = extract_language(name)
    with open(file_path, "rb") as f:
        source = f.read()
    return FileMetadata(name=name, file_path=file_path, language=language, package=None, imports=list(), body=source, hash=compute_file_hash(file_path))

