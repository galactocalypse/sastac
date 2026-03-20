import ollama
from sastac.config.loader import ConfigService
import json
import time
from pathlib import Path
from typing import Iterable
from dataclasses import dataclass, asdict
from typing import Optional
from .refiner import refine_task, RefineTaskRequest, RefinedTask
from sastac.llm.model import generate
from sastac.util.service import PackageDataService, InternalFileService
from sastac.context.context import ProjectContext, WorkspaceContext, TaskContext

planner_prompt = PackageDataService.read_text("sastac.files", "planning_prompt.txt")

@dataclass
class PlanningRequest:
    task: RefinedTask
    project_context: ProjectContext
    workspace_context: WorkspaceContext
    task_context: Optional[TaskContext] = None

@dataclass
class PlannedTask:
    task: str

def plan_task(planning_request: PlanningRequest) -> PlannedTask:
    start = time.time()
    InternalFileService.write_file("planner/input.log", planning_request.task.task)
    relevant_symbols = ""
    if planning_request.task_context:
        relevant_symbols = f"\n\n### Task-Specific Symbol Context\n{planning_request.task_context.formatted_context}"

    prompt = planner_prompt \
        .replace("{task}", planning_request.task.task) \
        .replace("{files}", planning_request.workspace_context.file_listing) \
        .replace("{project}", planning_request.project_context.project_readme) \
        .replace("{project_instructions}", planning_request.project_context.system_instructions) \
        .replace("{relevant_symbols}", relevant_symbols)

    InternalFileService.write_file("planner/prompt.log", prompt)
    response = generate(prompt, format={
        "type": "object",
        "properties": {
            "detailed_description": {
                "type": "string"
            },
            "relevant_files": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "relevant_modules": {
                "type": "object",
                "patternProperties": {
                    r"^[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+$": {
                        "type": "object",
                        "properties": {
                            "relevance_reason": {
                                "type": "string"
                            },
                            "files": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            }
                        },
                        "required": [
                            "relevance_reason",
                            "files"
                        ]
                    }
                },
                "additionalProperties": False
            },
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "module": {
                            "type": "string"
                        },
                        "file": {
                            "type": "string"
                        },
                        "file_relevance": {
                            "type": "string"
                        },
                        "description": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "module",
                        "file",
                        "file_relevance",
                        "description"
                    ]
                }
            }
        },
        "required": [
            "detailed_description",
            "relevant_files",
            "relevant_modules",
            "steps"
        ]
    })
    InternalFileService.write_file("planner/response.log", response.response)
    log = f"""
Input
Task: {planning_request.task.task}

Prompt:
{prompt}

Output
{response.response}
    """

    end = time.time()
    return PlannedTask(response.response)
