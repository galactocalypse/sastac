import json
import time
from dataclasses import dataclass, asdict
from sastac.llm.model import generate
from sastac.util.service import PackageDataService, InternalFileService
from .planner import PlannedTask
from sastac.context.context import ProjectContext, WorkspaceContext
from sastac.util.logger import logger

conveter_prompt = PackageDataService.read_text("sastac.files", "decomposition_prompt.txt")


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
    InternalFileService.write_file("execution_planner/input.log", execution_plan_request.planned_task.task)
    prompt = conveter_prompt \
        .replace("{plan}", execution_plan_request.planned_task.task) \
        .replace("{project}", execution_plan_request.project_context.project_readme) \
        .replace("{project_instructions}", execution_plan_request.project_context.system_instructions) \
        .replace("{files}", execution_plan_request.workspace_context.file_listing)
    InternalFileService.write_file("execution_planner/prompt.log", prompt)
    response = generate(prompt, prediction_length=1000, format={
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "tool": {
                    "type": "string",
                    "enum": ["read_file", "write_file", "run_script"]
                },
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string"
                        },
                        "content": {
                            "type": "string"
                        },
                        "command": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "tool",
                        "parameters"
                    ]
                }
            },
            "required": [
                "tool",
                "parameters"
            ]
        }
    })
    InternalFileService.write_file("execution_planner/response.log", response.response)
    end = time.time()
    cleaned = response.response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    return ExecutionPlan(json.loads(cleaned.strip()))
