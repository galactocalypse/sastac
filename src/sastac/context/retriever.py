from pathlib import Path
from typing import List
from sastac.context.context import TaskContext, WorkspaceContext
from sastac.storage.scopes.workspace_storage import WorkspaceStorage
from sastac.embedding.embedder import embed
from .workspace_indexer import WorkspaceIndexer
from sastac.util.logger import logger
from sastac.util.service import InternalFileService
from sastac.config.loader import ConfigService
from sastac.config.loader import ConfigService


cfg = ConfigService.load()


def retrieve_task_specific_context(
    workspace_id: str,
    base_dir: Path,
    task_description: str,
    storage: WorkspaceStorage,
    top_k: int = cfg.embeddings.top_k,
    score_threshold: float = cfg.embeddings.score_threshold
) -> TaskContext:
    """
    Refreshes the workspace index (JIT) and retrieves relevant code symbols
    from the vector store based on the task description.
    """
    # 1. Initialize Storage and Indexer
    indexer = WorkspaceIndexer(workspace_id, base_dir, embed, storage=storage)

    # 2. Refresh indices (Dynamic State & Index Refreshing)
    logger.debug(f"Refreshing workspace index for: {base_dir}")
    all_files = indexer.build(base_dir)

    # 3. Embed the task
    query_vector = embed(task_description)

    # 4. Query vector store for symbols
    logger.debug(f"Querying vector store for task: {task_description[:50]}...")
    scored_results = storage.vector.query(query_vector, top_k=top_k, score_threshold=score_threshold)
    relevant_symbols = [x['document'] for x in scored_results]
    logger.debug(f"Found {len(relevant_symbols)} relevant symbols with score >= {score_threshold}")

    # 5. Extract relevant files from symbols (Heuristic)
    relevant_files_set = set()
    for sym in relevant_symbols:
        path_str = sym.get("path")
        if path_str:
            relevant_files_set.add(Path(path_str))

    relevant_files = sorted(list(relevant_files_set))

    InternalFileService.write_file("vector_search/relevant_files.log", '\n'.join([str(x) for x in relevant_files]))
    InternalFileService.write_file("vector_search/relevant_symbols.log", '\n\n'.join([f'{x['document'].get("node_type")}: {x['document'].get("name")} ({x['score']})' for x in scored_results]))

    return TaskContext(
        relevant_files=relevant_files,
        relevant_symbols=relevant_symbols
    )
