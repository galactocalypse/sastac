# Task Context Refinement Plan

## 1. Evaluation of the Proposed Approach
The proposed plan to use structured symbol chunking for semantic retrieval is an **excellent** architectural approach. The current [WorkspaceContext](file:///home/adarsh/code/sastac/src/sastac/context/context.py#14-18) suffers from a scaling issue: it merely lists file paths (via [get_workspace_context](file:///home/adarsh/code/sastac/src/sastac/context/context.py#39-54)), which is relatively weak because the LLM planner lacks insight into the actual classes, functions, and logic inside those files without explicit tool calling to read them.

By doing task-specific retrieval *before* planning, we provide immediate, semantic context. This heavily reduces hallucination and the number of tool calls needed by the LLM to inspect the workspace. 

The three steps outlined in the proposal are sound:
1. **Retrieve Files**: Pre-filtering related files ensures that the planner only examines areas of the codebase likely to be impacted.
2. **Retrieve Symbols**: Using the vector store to fetch exact function/class signatures and docstrings gives the LLM precise semantic understanding of the tools existing in the codebase.
3. **Combine**: Injecting these together into the LLM context gives both a high-level view (files/modules) and a low-level view (methods/classes).

---

## 2. Implementation Strategy

Based on the existing codebase (which already includes [ChunkIndexer](file:///home/adarsh/code/sastac/src/sastac/ast/chunk_indexer.py#38-95), [CodeChunk](file:///home/adarsh/code/sastac/src/sastac/ast/chunker.py#15-42), [WorkspaceStorage](file:///home/adarsh/code/sastac/src/sastac/storage/scopes/workspace_storage.py#9-23), and [QdrantVectorStore](file:///home/adarsh/code/sastac/src/sastac/storage/backends/qdrant_vector.py#16-70)), we can operationalize the plan as follows:

### A. Dynamic State & Index Refreshing
To guarantee context is accurate without relying on full pre-indexing, we introduce dynamic refreshing:
1. **Refresh File Listings**: The workspace mappings and file listings should be evaluated and refreshed upon **starting the session** rather than being statically assumed.
2. **Just-In-Time (JIT) Symbol Embeddings**: When exploring files or preparing for task execution, we must track the modified timestamps (`mtime`) or file hashes of the codebase. If a file has been modified since it was last indexed, we immediately invoke `ChunkIndexer.index([file])` to re-extract and embed its symbols into the Vector Store before executing the retrieval query.

### B. Retrieve Key Modules/Files (KV Store / Heuristics)
Currently, `sastac.storage.backends.sqlite_kv.SQLiteKVStore` is available.
* **Mechanism**: We can store file-level metadata or module summaries in the KV store. 
* **Execution**: Either use a lightweight BM25/keyword search against the KV store or rely on the vector store hits (detailed below) to infer the most relevant files. If a symbol from [src/sastac/agent/refiner.py](file:///home/adarsh/code/sastac/src/sastac/agent/refiner.py) ranks high, that file is included in the relevant file list.

### C. Retrieve Structured Symbols (Vector Store)
The codebase already has an AST [ChunkIndexer](file:///home/adarsh/code/sastac/src/sastac/ast/chunk_indexer.py#38-95) that extracts [CodeChunk](file:///home/adarsh/code/sastac/src/sastac/ast/chunker.py#15-42) objects (functions, classes, etc.) and upserts them into the Qdrant vector store.
* **Mechanism**: Once the [refine_task](file:///home/adarsh/code/sastac/src/sastac/agent/refiner.py#26-67) step outputs a [RefinedTask](file:///home/adarsh/code/sastac/src/sastac/agent/refiner.py#20-25) (which contains `refined_task.task`), we convert that text into an embedding.
* **Execution**: 
  ```python
  from sastac.embedding.embedder import embed
  
  query_vector = embed(refined_task.task)
  top_symbols = workspace_storage.vector.query(query_vector, top_k=10)
  ```
  The results (`top_symbols`) will yield metadata dictionaries from the [CodeChunk](file:///home/adarsh/code/sastac/src/sastac/ast/chunker.py#15-42) objects (e.g., [name](file:///home/adarsh/code/sastac/src/sastac/ast/chunker.py#73-79), `node_type`, [signature](file:///home/adarsh/code/sastac/src/sastac/ast/chunker.py#99-104), [docstring](file:///home/adarsh/code/sastac/src/sastac/ast/chunker.py#81-97), `start_line`).

### D. Combine Contexts
We should update the domain models to hold these newly retrieved objects.
* **Mechanism**: Introduce a new `TaskContext` class or augment [WorkspaceContext](file:///home/adarsh/code/sastac/src/sastac/context/context.py#14-18) in [sastac/context/context.py](file:///home/adarsh/code/sastac/src/sastac/context/context.py).
* **Execution**:
  ```python
  @dataclass
  class TaskContext:
      relevant_files: list[Path]
      relevant_symbols: list[dict] # Contains signatures, docstrings, etc.
  ```
  Instead of injecting the entire workspace listing into the prompt, we format `TaskContext`:
  ```text
  Relevant Files:
  - src/sastac/agent/refiner.py
  - src/sastac/agent/workflow.py

  Relevant Symbols:
  - [Function] refine_task(request: RefineTaskRequest) -> RefinedTask
    Docstring: Refines the user's intent.
  ```

### E. Updating the Workflow ([workflow.py](file:///home/adarsh/code/sastac/src/sastac/agent/workflow.py))
In [sastac/agent/workflow.py](file:///home/adarsh/code/sastac/src/sastac/agent/workflow.py), currently the context is retrieved statically before refinement:
```python
workspace_context = get_workspace_context(Path("."))
```
We will shift this so that after [refine_task](file:///home/adarsh/code/sastac/src/sastac/agent/refiner.py#26-67) completes, we execute the retrieval:
```python
# 1. Refine Task
refined_task = retry(refine_task, ...)

# 2. Retrieve Context (New Step)
task_context = retrieve_task_specific_context(refined_task, workspace_context)

# 3. Plan Task
planning_request = PlanningRequest(refined_task, project_context, workspace_context, task_context)
planned_task = retry(plan_task, ...)
```

## 3. Conclusion
The proposed plan fits perfectly within the existing [WorkspaceStorage](file:///home/adarsh/code/sastac/src/sastac/storage/scopes/workspace_storage.py#9-23) and [CodeChunk](file:///home/adarsh/code/sastac/src/sastac/ast/chunker.py#15-42) infrastructure. It will make the LLM Planning step significantly more accurate by providing an immediate semantic "surroundings" view of the task.
