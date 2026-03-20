from pathlib import Path
from pydantic import BaseModel, Field
from typing import Iterable, List
from dataclasses import dataclass
from sastac.util.service import FileSystemService, PackageDataService
from sastac.storage.scopes.workspace_storage import WorkspaceStorage


@dataclass
class ProjectContext:
    base_directory: str
    system_instructions: str | None
    project_readme: str | None


@dataclass
class WorkspaceContext:
    files: list[Path]
    file_listing: str
    module_summaries: dict[str, str] = None # path -> summary


@dataclass
class ChatContext:
    messages: List[dict[str, str]] = Field(default_factory=list)

    def get_summary(self):
            return "\n".join([f"{message['role']}: {message['content']}" for message in self.messages if message['role'] != 'system'])


@dataclass
class TaskContext:
    relevant_files: list[Path]
    relevant_symbols: list[dict]
    
    @property
    def formatted_context(self) -> str:
        files_str = "\n".join([f"- {path}" for path in self.relevant_files])
        symbols_parts = []
        for sym in self.relevant_symbols:
            header = f"- [{sym.get('node_type', 'Symbol')}] {sym.get('signature', 'Unknown')} (File: {sym.get('path', 'Unknown')})"
            doc = f"  Docstring: {sym.get('docstring', 'None')}"
            body = sym.get('body', '')
            
            # Include body if it's small or if we want to provide implementation detail
            # For the planner, we might want to trim it to the first few lines or keep it if it's vital.
            # Let's include it but indented.
            body_str = ""
            if body:
                indented_body = "\n".join([f"    {line}" for line in body.split("\n")[:15]])
                body_str = f"\n  Implementation (first 15 lines):\n{indented_body}"
                if len(body.split("\n")) > 15:
                    body_str += "\n    ..."
            
            symbols_parts.append(f"{header}\n{doc}{body_str}")
            
        symbols_str = "\n\n".join(symbols_parts)
        return f"Relevant Files:\n{files_str}\n\nRelevant Symbols:\n{symbols_str}"


@dataclass
class SessionContext:
    project_id: str
    project_context: ProjectContext
    storage: WorkspaceStorage
    chat_context: ChatContext

    def send_message(self, role: str, message: str):
        self.chat_context.messages.append({"role": role, "content": message})


def get_system_prompt() -> dict[str, str]:
    base_chat_prompt = PackageDataService.read_text("sastac.files", "chat_prompt.txt")
    return {
        "role": "system",
        "content": base_chat_prompt
    }


def get_workspace_context(
    path: Path,
    excluded_dirs: Iterable[str] = (".venv", "__pycache__"),
    excluded_types: Iterable[str] = (".pyc",),
    prefix: str = "",
    storage: WorkspaceStorage | None = None
) -> WorkspaceContext:

    files = FileSystemService.get_workspace_files(
        path=path,
        excluded_dirs=excluded_dirs,
        excluded_types=excluded_types,
        prefix=prefix,
    )
    
    # Group by directory for a cleaner "Module Tree" view
    # Uses relative paths to keep context clean
    tree: dict[str, list[str]] = {}
    for f in files:
        rel_f = f.relative_to(path)
        parent = str(rel_f.parent)
        if parent == ".":
             parent = "root"
        if parent not in tree:
            tree[parent] = []
        tree[parent].append(rel_f.name)
    
    listing_parts = []
    summaries = {}
    for directory, filenames in sorted(tree.items()):
        files_in_dir = ", ".join(filenames)
        
        # Look up summary using the absolute path
        abs_dir = path / directory if directory != "root" else path
        
        summary_str = ""
        if storage:
            summary = storage.kv.get(f"summary:dir:{abs_dir}")
            if summary:
                summary_str = f" # {summary}"
                summaries[str(abs_dir)] = summary
                
        listing_parts.append(f"{directory}/ [{files_in_dir}]{summary_str}")
    
    listing = "\n".join(listing_parts)
    return WorkspaceContext(files, listing, module_summaries=summaries)
