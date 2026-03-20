from sastac.config.loader import ConfigService
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
from .refiner import refine_task, RefineTaskRequest
from .planner import PlannedTask, PlanningRequest, plan_task
from .execution_planner import ExecutionPlan, ExecutionPlanRequest, generate_execution_plan
from sastac.context.context import get_workspace_context
from sastac.util.service import PackageDataService
from .summarizer import summarize, ChatQuery, ChatResponse
from sastac.util.logger import logger
from sastac.util.retry import retry
from sastac.context.context import SessionContext, ProjectContext, TaskContext, get_system_prompt, ChatContext
from sastac.context.retriever import retrieve_task_specific_context
from sastac.storage.scopes.workspace_storage import WorkspaceStorage
from sastac.util.service import InternalFileService
from sastac.config.loader import ConfigService


cfg = ConfigService.load()
MAX_PLANNING_ATTEMPTS = 3
MAX_EXECUTION_PLANNING_ATTEMPTS = 3
MAX_REFINING_ATTEMPTS = 1
session_context = None

@dataclass
class TaskResponse:
    execution_plan: Optional[ExecutionPlan]
    chat_response: Optional[ChatResponse]


def initialize_session(project_id: str, base_directory: str):
    global session_context
    base_path = Path(base_directory)
    
    readme_path = base_path / "README.md"
    project_readme = readme_path.read_text("utf-8") if readme_path.exists() else None
    
    sastac_md_path = base_path / ".sastac" / "SASTAC.md"
    system_instructions = sastac_md_path.read_text("utf-8") if sastac_md_path.exists() else None

    project_context = ProjectContext(
        base_directory=base_directory,
        system_instructions=system_instructions,
        project_readme=project_readme
    )
    chat_context = ChatContext()
    chat_context.messages = [get_system_prompt()]
    session_context = SessionContext(
        project_id=project_id, 
        project_context=project_context,
        storage=WorkspaceStorage(project_id, base_path),
        chat_context=chat_context
    )
    

def process_task(user_input: str) -> TaskResponse:
    session_context.send_message("user", "user_input")
    task_response = TaskResponse(None, None)
    task_completed = False
    while not task_completed:
        chat_context = session_context.chat_context
        project_context = session_context.project_context
        storage = session_context.storage
        workspace_context = get_workspace_context(Path(project_context.base_directory), storage=storage)

        # 1. Refine
        logger.debug("Resolving intent for the given task")
        refining_request = RefineTaskRequest(chat_context, project_context, workspace_context, user_input)
        refined_task = retry(
            refine_task,
            MAX_REFINING_ATTEMPTS,
            "RefineTask",
            refining_request
        )
        logger.debug(f"Resolved intent for the given task to '{refined_task.intent}' in {refined_task.monitoring.get('duration')}s")
        
        # 2. Retrieve Task Context (Symbols & Files)
        task_context = None
        if refined_task.intent in ["workspace_mutation", "analysis"]:
            logger.debug(f"Retrieving task-specific context for: {refined_task.task[:50]}...")
            task_context = retrieve_task_specific_context(
                workspace_id=session_context.project_id,
                base_dir=Path(project_context.base_directory),
                task_description=refined_task.task,
                storage=storage,
                top_k=cfg.embeddings.top_k,
                score_threshold=cfg.embeddings.score_threshold
            )

        # 3. Route
        if refined_task.intent == "workspace_mutation":
            # Plan
            planning_request = PlanningRequest(
                task=refined_task, 
                project_context=project_context, 
                workspace_context=workspace_context,
                task_context=task_context
            )
            planned_task = retry(
                plan_task, 
                MAX_PLANNING_ATTEMPTS, 
                "PlanTask", 
                planning_request
            )
            
            # Resolve execution plan
            exection_plan_request = ExecutionPlanRequest(planned_task, project_context, workspace_context)
            task_response.execution_plan = retry(
                generate_execution_plan, 
                MAX_EXECUTION_PLANNING_ATTEMPTS, 
                "CreateExecutionPlan", 
                exection_plan_request
            )

        elif refined_task.intent == "conceptual":
            # Respond
            chat_query = ChatQuery(
                task=refined_task, 
                project_context=project_context, 
                workspace_context=workspace_context
            )
            task_response.chat_response = summarize(session_context, chat_query)

        elif refined_task.intent == "analysis":
            # Respond
            chat_query = ChatQuery(
                task=refined_task, 
                project_context=project_context, 
                workspace_context=workspace_context,
                task_context=task_context
            )
            task_response.chat_response = summarize(session_context, chat_query)
        else:
            raise Exception(f"Unsupported intent: {refined_task.intent}")

        # apply tool_calls
        # validate
        task_completed = True

    InternalFileService.write_file("chat.json", json.dumps(session_context.chat_context.messages[1:], indent=True))
    return task_response
    
