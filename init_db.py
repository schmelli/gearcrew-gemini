import sqlite3
import os
import asyncio
from cognee.infrastructure.databases.relational import create_db_and_tables

async def init_db():
    print("Initializing Cognee DB...")
    await create_db_and_tables()
    
    base_path = "venv/lib/python3.11/site-packages/cognee/.cognee_system/databases"
    db_file = os.path.join(base_path, "cognee_db")
    
    # Try to connect
    print(f"Connecting to {db_file}...")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Create table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS sync_operations (
        id VARCHAR(36) PRIMARY KEY,
        run_id VARCHAR(36),
        status VARCHAR(50),
        progress_percentage INTEGER,
        dataset_ids TEXT,
        dataset_names TEXT,
        user_id VARCHAR(36),
        created_at DATETIME,
        started_at DATETIME,
        completed_at DATETIME,
        total_records_to_sync INTEGER,
        total_records_to_download INTEGER,
        total_records_to_upload INTEGER,
        records_downloaded INTEGER,
        records_uploaded INTEGER,
        bytes_downloaded INTEGER,
        bytes_uploaded INTEGER,
        dataset_sync_hashes TEXT,
        error_message TEXT,
        retry_count INTEGER
    );
    """
    cursor.execute("DROP TABLE IF EXISTS sync_operations")
    cursor.execute(create_table_sql)
    conn.commit()
    print("Table sync_operations created.")
    conn.close()

if __name__ == "__main__":
    asyncio.run(init_db())
