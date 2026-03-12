from sastac.config.loader import ConfigService
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
from .refiner import refine_task, RefineTaskRequest
from .planner import PlannedTask, PlanningRequest, plan_task
from .execution_planner import ExecutionPlan, ExecutionPlanRequest, generate_execution_plan
from sastac.context.context import get_chat_context, get_workspace_context
from sastac.llm.model import send_message
from sastac.util.service import PackageDataService
from .summarizer import summarize, ChatQuery, ChatResponse
from sastac.util.logger import logger
from sastac.util.retry import retry
from sastac.context.context import SessionContext, ProjectContext

MAX_PLANNING_ATTEMPTS = 3
MAX_EXECUTION_PLANNING_ATTEMPTS = 3
MAX_REFINING_ATTEMPTS = 3
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
    session_context = SessionContext(project_id, project_context)

def initialize_chat():
    base_chat_prompt = PackageDataService.read_text("sastac.files", "chat_prompt.txt")
    send_message("system", base_chat_prompt)
    logger.debug("Chat initialized with system prompt")
    

def process_task(user_input: str) -> TaskResponse:
    task_response = TaskResponse(None, None)
    task_completed = False
    while not task_completed:
        chat_context = get_chat_context()
        project_context = session_context.project_context
        workspace_context = get_workspace_context(Path("."))

        # Refine
        logger.debug("Resolving intent for the given task")
        refining_request = RefineTaskRequest(chat_context, project_context, workspace_context, user_input)
        refined_task = retry(
            refine_task,
            MAX_REFINING_ATTEMPTS,
            "RefineTask",
            refining_request
        )
        logger.debug(f"Resolved intent for the given task to '{refined_task.intent}' in {refined_task.monitoring.get('duration')}s")
        
        # Route
        if refined_task.intent == "workspace_mutation":
            # Plan
            planning_request = PlanningRequest(refined_task, project_context, workspace_context)
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
            chat_query = ChatQuery(refined_task, project_context, workspace_context)
            task_response.chat_response = summarize(chat_query)

        elif refined_task.intent == "analysis":
            raise Exception("Code analysis is currently not supported")

        # apply tool_calls
        # validate
        task_completed = True

    return task_response
    
