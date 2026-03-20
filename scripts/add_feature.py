import sys
import os

# Add the 'src' directory to the Python path to allow importing the 'sastac' package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from sastac.agent.workflow import process_task, initialize_session
from sastac.util.service import FileService
import json
from dataclasses import asdict

if __name__ == "__main__":
    initialize_session("sastac", "/home/adarsh/code/sastac")
    task_response = process_task("Add a module to manage dependency graphs of packages. Should be able to build the dependency graph from scratch and update incrementally. Should then populate dependency graph context in the task context.")
    if task_response.chat_response:
        FileService.write_file("response.txt", task_response.chat_response.response)
    elif task_response.execution_plan:
        FileService.write_file("plan.txt", json.dumps(asdict(task_response.execution_plan)))
    else:
        raise Exception(f"Could not respond to task")
