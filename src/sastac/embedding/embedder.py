import ollama
from typing import Union, List
from sastac.config.loader import ConfigService
from sastac.util.logger import logger

cfg = ConfigService.load()
_model = cfg.embeddings.model

# Optional: create a persistent client (slightly faster for many calls)
_client = ollama.Client()

def embed(text: Union[str, List[str]]):
    """
    Supports:
      - single string → returns list[float] (1024-dim)
      - list of strings → returns list[list[float]]
    """
    # Normalize input so Ollama always gets a list
    if isinstance(text, str):
        input_texts = [text]
    else:
        input_texts = text

    try:
        response = _client.embed(
            model=_model,
            input=input_texts
        )
    except Exception as e:
        logger.error(f"Model: {_model}")
        logger.error(f"input: {input_texts}")
        logger.error(f"Error embedding text: {e}")
        raise e

    embeddings = response["embeddings"]

    # Return the exact same format your old code produced
    return embeddings[0] if isinstance(text, str) else embeddings
