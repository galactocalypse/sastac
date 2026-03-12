from sastac.ast.processor.file_processor import get_file_meta
from sastac.ast.chunker import extract_symbol_chunks
from sastac.storage.scopes.workspace_storage import WorkspaceStorage
from pathlib import Path

def index_file(workspace_id, file_path):
    file_meta = get_file_meta(file_path)
    symbols = extract_symbol_chunks(file_meta)
    storage = WorkspaceStorage(workspace_id, Path("~/.sastac"))
    storage.vector.upsert()



if __name__ == "__main__":
    file_path = "/home/adarsh/code/booklore/booklore-api/src/main/java/org/booklore/config/security/SecurityConfig.java"
    index_file(file_path)
