import ollama
from sastac.config.loader import load_config
import json
import time
from pathlib import Path
from typing import Iterable
from dataclasses import dataclass, asdict
from typing import Optional
from .refiner import refine_task, RefineTaskRequest
from .model import read_file, generate
from .planner import PlannedTask
from .context import ProjectContext, WorkspaceContext

conveter_prompt = read_file("src/sastac/llm/decomposition_prompt.txt")


@dataclass
class ExecutionPlanRequest:
    planned_task: PlannedTask
    project_context: ProjectContext
    workspace_context: WorkspaceContext

@dataclass
class ExecutionPlan:
    steps: list[dict[str, object]]


def generate_execution_plan(execution_plan_request: ExecutionPlanRequest) -> ExecutionPlan:
    start = time.time()
    prompt = conveter_prompt \
        .replace("{plan}", execution_plan_request.planned_task.task) \
        .replace("{project}", execution_plan_request.project_context.description) \
        .replace("{files}", execution_plan_request.workspace_context.file_listing)
    response = generate(prompt)
    end = time.time()
    print(f"Decomposer duration: {end-start}s.")
    return ExecutionPlan(json.loads(response.response))
