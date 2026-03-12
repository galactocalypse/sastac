from sastac.agent.workflow import initialize_chat, process_task, initialize_session
from sastac.util.service import FileService
import json
from dataclasses import asdict

if __name__ == "__main__":
    initialize_session("sastac", "/home/adarsh/code/sastac")
    initialize_chat()
    task_response = process_task("Implement a file chunking module")
    if task_response.chat_response:
        FileService.write_file("response.txt", task_response.chat_response.response)
    elif task_response.execution_plan:
        FileService.write_file("plan.txt", json.dumps(asdict(task_response.execution_plan)))
    else:
        raise Exception(f"Could not respond to task")
