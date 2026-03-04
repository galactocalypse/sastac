from sastac.config.loader import load_config
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
from .refiner import refine_task, RefineTaskRequest
from .planner import PlannedTask, PlanningRequest, plan_task
from .execution_planner import ExecutionPlan, ExecutionPlanRequest, generate_execution_plan
from .context import get_chat_context, get_project_context, get_workspace_context
from .model import read_file, send_message, write_file
from .summarizer import summarize, ChatQuery, ChatResponse


@dataclass
class TaskResponse:
    execution_plan: Optional[ExecutionPlan]
    chat_response: Optional[ChatResponse]

def initialize_chat():
    base_chat_prompt = read_file("src/sastac/llm/chat_prompt.txt")
    send_message("system", base_chat_prompt)
    

def process_task(user_input: str) -> TaskResponse:
    task_response = TaskResponse(None, None)
    task_completed = False
    while not task_completed:
        chat_context = get_chat_context()
        project_context = get_project_context()
        workspace_context = get_workspace_context(Path("."))

        # Refine
        refining_request = RefineTaskRequest(chat_context, project_context, workspace_context, user_input)
        refined_task = refine_task(refining_request)
        
        # Route
        if refined_task.requires_tools:
            # Plan
            planning_request = PlanningRequest(refined_task, project_context, workspace_context)
            planned_task = plan_task(planning_request)
            
            # Resolve execution plan
            exection_plan_request = ExecutionPlanRequest(planned_task, project_context, workspace_context)
            task_response.execution_plan = generate_execution_plan(exection_plan_request)
            
        else:
            # Respond
            chat_query = ChatQuery(refined_task, project_context, workspace_context)
            task_response.chat_response = summarize(chat_query)

        # apply tool_calls
        # validate
        task_completed = True

    return task_response
    

if __name__ == "__main__":
    task_response = process_task("Implement a file chunking module")
    if task_response.chat_response:
        write_file("response.txt", task_response.chat_response.response)
    elif task_response.execution_plan:
        write_file("plan.txt", json.dumps(asdict(task_response.execution_plan)))
    else:
        raise Exception(f"Could not respond to task")
