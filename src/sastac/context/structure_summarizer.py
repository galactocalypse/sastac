from pathlib import Path
from sastac.llm.model import generate
from sastac.storage.scopes.workspace_storage import WorkspaceStorage
from sastac.util.logger import logger

class StructureSummarizer:
    def __init__(self, storage: WorkspaceStorage):
        self.storage = storage

    def summarize_directory(self, directory: Path, files: list[Path]) -> str:
        """Generates a high-level summary of a directory based on its files."""
        key = f"summary:dir:{directory}"
        
        # Check if we already have it
        # (In a real scenario, we'd check if any files in this dir changed)
        # For now, let's allow re-generation.
        
        file_list = "\n".join([f.name for f in files])
        
        prompt = f"""
        Summarize the purpose of the following directory in a single concise sentence.
        Focus on what the module responsible for.
        
        Directory: {directory}
        Files:
        {file_list}
        
        Summary:
        """
        
        try:
            response = generate(prompt, prediction_length=100)
            summary = response.response.strip()
            self.storage.kv.set(key, summary)
            return summary
        except Exception as e:
            logger.error(f"Failed to summarize directory {directory}: {e}")
            return "No summary available."

    def get_summary(self, directory: Path) -> str | None:
        return self.storage.kv.get(f"summary:dir:{directory}")
