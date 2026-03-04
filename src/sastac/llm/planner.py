import ollama
from sastac.config.loader import load_config
import json
import time
from pathlib import Path
from typing import Iterable
from dataclasses import dataclass, asdict
from typing import Optional
from .refiner import refine_task, RefineTaskRequest, RefinedTask
from .model import read_file, generate
from .context import ProjectContext, WorkspaceContext

planner_prompt = read_file("src/sastac/llm/planning_prompt.txt")

@dataclass
class PlanningRequest:
    task: RefinedTask
    project_context: ProjectContext
    workspace_context: WorkspaceContext

@dataclass
class PlannedTask:
    task: str

def plan_task(planning_request: PlanningRequest) -> PlannedTask:
    start = time.time()
    prompt = planner_prompt \
        .replace("{refined_task_json}", json.dumps(asdict(planning_request.task))) \
        .replace("{files}", planning_request.workspace_context.file_listing) \
        .replace("{project}", planning_request.project_context.description)

    response = generate(prompt)
    end = time.time()
    return PlannedTask(response.response)
