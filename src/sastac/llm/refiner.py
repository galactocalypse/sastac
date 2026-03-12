import json
import time
from dataclasses import dataclass
from .model import read_file, generate
from .context import ProjectContext, WorkspaceContext, ChatContext


refiner_prompt = read_file("src/sastac/llm/refinement_prompt.txt")

@dataclass
class RefineTaskRequest:
    chat_context: ChatContext
    project_context: ProjectContext
    workspace_context: WorkspaceContext
    user_input: str

@dataclass
class RefinedTask:
    intent: str
    requires_tools: bool
    task: str
    constraints: list[str]
    assumptions: list[str]
    requires_clarification: bool
    
def refine_task(refinement_task: RefineTaskRequest) -> RefinedTask:

    start = time.time()
    prompt = refiner_prompt \
        .replace("{chat_summary}", refinement_task.chat_context.summary) \
        .replace("{task}", refinement_task.user_input) \
        .replace("{project}", refinement_task.project_context.description) \
        .replace("{files}", refinement_task.workspace_context.file_listing)
    
    prediction_length = 100
    task_length = len(refinement_task.user_input.split(" "))
    if task_length > 200:
        prediction_length = 500

    response = generate(prompt, prediction_length)
    
    end = time.time()
    print(f"Refiner duration: {end-start}s.")
    return RefinedTask(**json.loads(response.response))
