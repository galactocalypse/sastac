import ollama
from sastac.config.loader import ConfigService
import time
from dataclasses import dataclass


@dataclass
class LLMInvocation:
    prompt: str
    response: str
    duration_seconds: float


cfg = ConfigService.load()


messages: list[dict[str, str]] = []

def generate(prompt: str, prediction_length = 400, format: str | dict[str, object] = "json") -> LLMInvocation:
    start = time.time()
    response = ollama.generate(
        model=cfg.task_refiner.model,
        prompt=prompt,
        options={
            "temperature": cfg.task_refiner.temperature,
            "num_predict": 800,
            "format": format
        }
    )
    end = time.time()
    return LLMInvocation(prompt, response.response, end - start)


def get_chat_response(messages: list[dict[str, str]]) -> LLMInvocation:
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
    end = time.time()
    return LLMInvocation(prompt, response["message"]["content"], end - start)
