from pathlib import Path

CODE_EXTENSIONS = {".py", ".java", ".go", ".rs", ".js", ".ts", ".tsx"}

def scan_repo(root):
    return [
        str(p)[len(root):] for p in Path(root).rglob("*")
        if p.suffix in CODE_EXTENSIONS
    ]

def get_file_inventory(source_dir):
    pass


def preprocess(root):
    files = scan_repo(root)
    for file in files:
        print(file)
