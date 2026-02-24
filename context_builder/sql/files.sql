CREATE TABLE IF NOT EXISTS files (
    project_id TEXT NOT NULL,
    path TEXT NOT NULL,
    language TEXT,
    size INTEGER NOT NULL,
    last_modified INTEGER NOT NULL,
    PRIMARY KEY (project_id, path)
);

CREATE INDEX IF NOT EXISTS idx_files_project
ON files (project_id);
