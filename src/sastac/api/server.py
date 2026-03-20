import os
import uuid
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from .schemas import (
    Model, ModelList, ChatCompletionRequest, 
    ChatCompletionResponse, ChatCompletionChoice, ChatMessage, ChatCompletionUsage
)
from sastac.agent.workflow import process_task, initialize_session
from sastac.util.logger import logger

import asyncio

app = FastAPI(title="sastac OpenAI-Compliant API")

# Global state to track if session is initialized
SESSION_INITIALIZED = False
SESSION_LOCK = asyncio.Lock()

async def ensure_session():
    global SESSION_INITIALIZED
    if not SESSION_INITIALIZED:
        async with SESSION_LOCK:
            if not SESSION_INITIALIZED: # Double check pattern
                project_id = os.environ.get("SASTAC_PROJECT_ID", "default-api-project")
                base_dir = os.environ.get("SASTAC_BASE_DIR", os.getcwd())
                logger.info(f"Initializing sastac session for project {project_id} at {base_dir}")
                initialize_session(project_id, base_dir)
                SESSION_INITIALIZED = True

@app.get("/v1/models", response_model=ModelList)
async def list_models():
    return ModelList(data=[
        Model(id="sastac-agent", owned_by="sastac")
    ])

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    try:
        await ensure_session()
    except Exception as e:
        if "already accessed by another instance" in str(e):
            raise HTTPException(
                status_code=503, 
                detail="Qdrant storage is locked by another instance. Please ensure no other sastac processes are running."
            )
        raise HTTPException(status_code=500, detail=f"Failed to initialize session: {str(e)}")
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty")
    
    # Get the last message from the user
    user_message = request.messages[-1].content
    logger.debug(f"Received chat completion request: {user_message}")
    
    try:
        # Process task via agent workflow
        response = process_task(user_message)
        
        # Determine the content to return
        content = ""
        if response.chat_response:
            content = response.chat_response.response
        elif response.execution_plan:
            content = f"Execution plan generated:\n{response.execution_plan.goals_description}"
        else:
            content = "Task processed successfully, but no specific response was generated."

        # Format as OpenAI response
        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4()}",
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=content)
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=len(user_message) // 4, # Rough estimate
                completion_tokens=len(content) // 4,
                total_tokens=(len(user_message) + len(content)) // 4
            )
        )
    except Exception as e:
        logger.error(f"Error processing task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
