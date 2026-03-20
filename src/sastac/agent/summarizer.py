import ollama
from sastac.config.loader import ConfigService
import json
import time
from pathlib import Path
from typing import Iterable
from dataclasses import dataclass, asdict
from typing import Optional
from .refiner import RefinedTask
from sastac.context.context import ChatContext, ProjectContext, WorkspaceContext, TaskContext, SessionContext
from sastac.llm.model import get_chat_response, generate
from sastac.util.logger import logger



@dataclass
class ChatQuery:
    task: RefinedTask
    project_context: ProjectContext
    workspace_context: WorkspaceContext
    task_context: Optional[TaskContext] = None


@dataclass
class ChatResponse:
    response: str

def summarize(session_context: SessionContext, query: ChatQuery) -> ChatResponse:
    start = time.time()
    logger.debug(f"Generating chat response for: {query.task.task[:50]}...")
    
    additional_context = ""
    if query.task_context:
        additional_context = f"\n\n### Task-Specific Context\n{query.task_context.formatted_context}"

    message = f"""
    Answer the following question based on the updated project context provided:
Query: {query.task.task}

Project context (Readme):
{query.project_context.project_readme or "No readme found"}

Project context (Instructions):
{query.project_context.system_instructions or "No instructions found"}

Workspace context:
{query.workspace_context.file_listing}
{additional_context}
"""
    response = generate(message, prediction_length=800)
    session_context.send_message("assistant", response.response)
    end = time.time()
    return ChatResponse(response.response)
