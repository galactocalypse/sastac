import argparse
from pathlib import Path
from sentence_transformers import SentenceTransformer

from sastac.index.workspace_indexer import WorkspaceIndexer
from sastac.embedding.embedder import  embed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace_id")
    parser.add_argument("root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise ValueError(f"Workspace root not found: {root}")

    base_dir = Path.home() / ".sastac"

    indexer = WorkspaceIndexer(args.workspace_id, base_dir, embed)
    indexer.build(root)


if __name__ == "__main__":
    main()
