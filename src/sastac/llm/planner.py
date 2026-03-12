import ollama
from sastac.config.loader import load_config
import json
import time
from pathlib import Path
from typing import Iterable
from dataclasses import dataclass, asdict
from typing import Optional
from .refiner import refine_task, RefineTaskRequest, RefinedTask
from .model import read_file, generate, write_file
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
        .replace("{task}", planning_request.task.task) \
        .replace("{constraints}", "\n - ".join(planning_request.task.constraints)) \
        .replace("{files}", planning_request.workspace_context.file_listing) \
        .replace("{project}", planning_request.project_context.description)

    response = generate(prompt)
    log = f"""
Input
Requires clarification: {planning_request.task.requires_clarification}
Requires tools: {planning_request.task.requires_tools}
Task: {planning_request.task.task}
Constraints:
{"\n - ".join(planning_request.task.constraints) or "No additional constraints"}
Assumptions:
{"\n - ".join(planning_request.task.assumptions) or "No assumptions"}

Prompt:
{prompt}

Output
{response.response}
    """
    write_file("logs/plan.log", log)
    end = time.time()
    return PlannedTask(response.response)
