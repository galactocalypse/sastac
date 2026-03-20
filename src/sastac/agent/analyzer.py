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
from sastac.llm.model import generate
from sastac.util.logger import logger
from sastac.util.service import PackageDataService, InternalFileService
from .summarizer import ChatQuery, ChatResponse

analyzer_prompt = PackageDataService.read_text("sastac.files.prompts", "analyzer.txt")

def analyze(session_context: SessionContext, query: ChatQuery) -> ChatResponse:
    start = time.time()
    logger.debug(f"Generating chat response for: {query.task.task[:50]}...")
    prompt = analyzer_prompt.replace("{query}", query.task.task)
    context = f"""
<project_context>
{query.project_context.project_readme or "No readme found"}
</project_context>

<project_instructions>
{query.project_context.system_instructions or "No instructions found"}
</project_instructions>

<workspace_context>
{query.workspace_context.file_listing}
</workspace_context>

<relevant_files>
{"\n- ".join([str(x) for x in query.task_context.relevant_files])}
</relevant_files>

<relevant_symbols>
{query.task_context.formatted_context}
</relevant_symbols>
"""
    prompt = prompt.replace("{context}", context)
    InternalFileService.write_file("analyzer/prompt.log", prompt)
    response = generate(prompt, prediction_length=1000)
    session_context.send_message("assistant", response.response)
    InternalFileService.write_file("analyzer/response.log", response.response)
    end = time.time()
    return ChatResponse(response.response)
