import ollama
from typing import Union, List
from sastac.config.loader import load_config

cfg = load_config()

# Model name – make sure your config file sets this to "bge-m3"
# (you can keep the same cfg.embeddings.model key – just change the value)
_model = cfg.embeddings.model   # e.g. "bge-m3"

# Optional: create a persistent client (slightly faster for many calls)
_client = ollama.Client()

def embed(text: Union[str, List[str]]):
    """
    Generate embeddings using Ollama + bge-m3.
    This is a **drop-in replacement** for your old SentenceTransformer.encode() call.
    
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
        print(f"Model: {_model}")
        print(f"input: {input_texts}")
        response = _client.embed(
            model=_model,
            input=input_texts
        )
    except Exception as e:
        print(f"Error embedding text: {e}")
        raise

    embeddings = response["embeddings"]

    # Return the exact same format your old code produced
    return embeddings[0] if isinstance(text, str) else embeddings
