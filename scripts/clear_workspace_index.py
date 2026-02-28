import argparse
import shutil
from pathlib import Path


def clear_workspace(workspace_id: str, base_dir: Path):

    ws_root = base_dir / "workspaces" / workspace_id

    if not ws_root.exists():
        print("Workspace index does not exist.")
        return

    print(f"Deleting index at {ws_root}")
    shutil.rmtree(ws_root)
    print("Done.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace_id")
    parser.add_argument("--storage", default="~/.sastac")

    args = parser.parse_args()
    base = Path(args.storage).expanduser()

    clear_workspace(args.workspace_id, base)


if __name__ == "__main__":
    main()
