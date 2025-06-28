import sqlite3
import json

# Optional from the typing module: return type can be a specific type or None.
from typing import Optional

# decorator from the dataclasses module, 
# which simplifies class creation by automatically generating methods like __init__ for data storage classes.
from dataclasses import dataclass

################################################################
### Define SQLite database file in Render, different from local environment.
### and /app is not writable, recommended to use tmp/
# DB_FILE = "./db/registration.db"
DB_FILE = "/tmp/registration.db"
##################################################################



# @dataclass decorator automatically generates an __init__ method 
# to initialize these attributes, 
# along with other methods like __repr__.
@dataclass
class RegistrationState:
    session_id: str
    collected_data: dict
    current_question: str
    current_node: str

import os
def init_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                collected_data TEXT,
                current_question TEXT,
                current_node TEXT
            )
            """
        )
        conn.commit()

# Insert or update a session in SQLite
def upsert_session_to_db(session_id: str,
                         collected_data: dict,
                         current_question: str,
                         current_node: str
                         ):

    collected_data_json = json.dumps(collected_data) # Converts the collected_data dictionary to a JSON string using json.dumps
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessions (session_id, collected_data, current_question, current_node)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                collected_data = excluded.collected_data,
                current_question = excluded.current_question,
                current_node = excluded.current_node
            """,
            (session_id, collected_data_json, current_question, current_node), # a tuple containing the values that will replace the ? placeholders in the SQL INSERT statement.
        )
        conn.commit()

# Fetch a session from SQLite & return as a dictionary
def fetch_session_from_db(session_id: str) -> Optional[dict]:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT session_id, collected_data, current_question, current_node FROM sessions WHERE session_id = ?",
            (session_id,),
        )
        result = cursor.fetchone()

    if result:
        session_id, collected_data_json, current_question, current_node = result
        collected_data = json.loads(collected_data_json)
        return {
            "session_id": session_id,
            "collected_data": collected_data,
            "current_question": current_question,
            "current_node": current_node,
        }
    return None

# Initialize database on import
init_db()