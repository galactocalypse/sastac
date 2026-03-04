import ollama
from sastac.config.loader import load_config
import time
from dataclasses import dataclass


@dataclass
class LLMInvocation:
    prompt: str
    response: str
    duration_seconds: float


@dataclass
class PhaseResponse:
    name: str
    llm_response: LLMInvocation
    task: dict[str, str]
    result: dict[str, object]
    duration_seconds: float


def read_file(path):
    with open(path, "r") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

cfg = load_config()
base_chat_prompt = read_file("src/sastac/llm/chat_prompt.txt")
refiner_prompt = read_file("src/sastac/llm/refinement_prompt.txt")
planner_prompt = read_file("src/sastac/llm/planning_prompt.txt")
conveter_prompt = read_file("src/sastac/llm/decomposition_prompt.txt")

messages: list[dict[str, str]] = []

def generate(prompt: str, prediction_length = 400) -> LLMInvocation:
    start = time.time()
    response = ollama.generate(
        model=cfg.task_refiner.model,
        prompt=prompt,
        options={
            "temperature": cfg.task_refiner.temperature,
            "num_predict": 800,
        }
    )
    end = time.time()
    return LLMInvocation(prompt, response.response, end - start)

def get_chat_response() -> LLMInvocation:
    start = time.time()
    prompt = messages[-1]["content"]
    response = ollama.chat(
        model=cfg.task_refiner.model,
        messages=messages,
        options={
            "temperature": cfg.task_refiner.temperature,
            "num_predict": 800,
        }
    )
    send_message("system", response["message"]["content"])
    end = time.time()
    return LLMInvocation(prompt, response["message"]["content"], end - start)


def send_message(role: str, message: str):
    messages.append({
        "role": role,
        "content": message
    })
