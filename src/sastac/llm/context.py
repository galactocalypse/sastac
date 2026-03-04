from pathlib import Path
from typing import Iterable
from dataclasses import dataclass
from .model import read_file
from sastac.fs.service import FileSystemService


@dataclass
class ProjectContext:
    description: str

@dataclass
class WorkspaceContext:
    files: list[Path]
    file_listing: str

@dataclass
class ChatContext:
    messages: list[dict[str, str]]
    summary: str

base_chat_prompt = read_file("src/sastac/llm/chat_prompt.txt")
messages: list[dict[str, str]] = [{
    "role": "system",
    "content": base_chat_prompt
}]


def get_project_context() -> ProjectContext:
    return ProjectContext("""
        Sastac (Sasta ClaudeCode)
        This project implements an AI coding assistant in Python.
        It uses tree-sitter for AST parsing, ollama for accessing LLM and embedding models,
        qdrant for vector DB, and sqlite for other storage.
        """)

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
    chat_summary = "\n".join([f"{message["role"]}: {message["content"]}" for message in messages])
    return ChatContext(messages, chat_summary)

