from pathlib import Path
from typing import Iterable
from dataclasses import dataclass
from sastac.util.service import FileSystemService, PackageDataService


@dataclass
class ProjectContext:
    base_directory: str
    system_instructions: str | None
    project_readme: str | None


@dataclass
class WorkspaceContext:
    files: list[Path]
    file_listing: str


@dataclass
class ChatContext:
    messages: list[dict[str, str]]
    summary: str


@dataclass
class SessionContext:
    project_id: str
    project_context: ProjectContext


base_chat_prompt = PackageDataService.read_text("sastac.files", "chat_prompt.txt")
messages: list[dict[str, str]] = [{
    "role": "system",
    "content": base_chat_prompt
}]


def get_workspace_context(
    path: Path,
    excluded_dirs: Iterable[str] = [".venv", "__pycache__"],
    excluded_types: Iterable[str] = [".pyc"],
    prefix: str = "src"
) -> WorkspaceContext:

    filter_fn = lambda path: (
        not any(dir_name in path.parts for dir_name in excluded_dirs) and
        not any(path.suffix == ext for ext in excluded_types) and
        str(path).startswith(prefix)
    )
    files = FileSystemService.list_files(path, filter_fn=filter_fn)
    listing = "\n".join([str(file) for file in files])
    return WorkspaceContext(files, listing)


def get_chat_context() -> ChatContext:
    chat_summary = "\n".join([f"{message["role"]}: {message["content"]}" for message in messages if message["role"] != "system"])
    return ChatContext(messages[1:], chat_summary)

