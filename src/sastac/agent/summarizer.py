import ollama
from sastac.config.loader import load_config
import json
import time
from pathlib import Path
from typing import Iterable
from dataclasses import dataclass, asdict
from typing import Optional
from .refiner import RefinedTask
from .context import ChatContext, ProjectContext, WorkspaceContext
from .model import get_chat_response, send_message



@dataclass
class ChatQuery:
    task: RefinedTask
    project_context: ProjectContext
    workspace_context: WorkspaceContext


@dataclass
class ChatResponse:
    response: str

def summarize(query: ChatQuery) -> ChatResponse:
    start = time.time()
    
    message = f"""
    Answer the following question based on the updated project context provided:
Query: {query.task.task}

Project context:
{query.project_context.description}

Workspace context:
{query.workspace_context.file_listing}
"""
    
    send_message("user", message)
    response = get_chat_response()
    end = time.time()
    return ChatResponse(response.response)
