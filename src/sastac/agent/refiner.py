import json
import time
from dataclasses import dataclass
from typing import Optional
from sastac.llm.model import generate
from sastac.util.service import PackageDataService
from sastac.context.context import ProjectContext, WorkspaceContext, ChatContext
from sastac.util.service import InternalFileService
from sastac.util.logger import logger

refiner_prompt = PackageDataService.read_text("sastac.files", "refinement_prompt.txt")

@dataclass
class RefineTaskRequest:
    chat_context: ChatContext
    project_context: ProjectContext
    workspace_context: WorkspaceContext
    user_input: str

@dataclass
class RefinedTask:
    intent: str
    task: str
    monitoring: Optional[dict[str, float | str]] = None
    
def refine_task(request: RefineTaskRequest) -> RefinedTask:

    start = time.time()
    InternalFileService.write_file("refiner/input.log", request.user_input)
    prompt = refiner_prompt \
        .replace("{chat_summary}", request.chat_context.get_summary() or "-") \
        .replace("{task}", request.user_input) \
        .replace("{project_instructions}", request.project_context.system_instructions) \
        .replace("{project}", request.project_context.project_readme) \
        .replace("{files}", request.workspace_context.file_listing)
    
    InternalFileService.write_file("refiner/prompt.log", prompt)
    prediction_length = 100
    task_length = len(request.user_input.split(" "))
    if task_length > 200:
        prediction_length = 500

    response = generate(prompt, prediction_length, format={
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": ["conceptual", "analysis", "workspace_mutation"]
            },
            "task": {
                "type": "string"
            }
        }})
    InternalFileService.write_file("refiner/response.log", response.response)
    end = time.time()
    response_data = json.loads(response.response)
    if "monitoring" not in response_data:
        response_data["monitoring"] = {}
    
    refined_task = RefinedTask(**response_data)
    
    if refined_task.monitoring is None:
        refined_task.monitoring = {}
        
    refined_task.monitoring["duration"] = end - start
    return refined_task
