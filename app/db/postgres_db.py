from dataclasses import dataclass
import psycopg2
import json
from typing import Optional
from helpers.config import DATABASE_URL

@dataclass
class RegistrationState:
    session_id: str
    collected_data: dict
    current_question: str
    current_node: str

def init_db():
    with psycopg2.connect(DATABASE_URL) as conn:
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

def upsert_session_to_db(session_id: str, collected_data: dict, current_question: str, current_node: str):
    collected_data_json = json.dumps(collected_data)
    with psycopg2.connect(DATABASE_URL) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO sessions (session_id, collected_data, current_question, current_node)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (session_id) DO UPDATE SET
                collected_data = EXCLUDED.collected_data,
                current_question = EXCLUDED.current_question,
                current_node = EXCLUDED.current_node
            """,
            (session_id, collected_data_json, current_question, current_node),
        )
        conn.commit()

def fetch_session_from_db(session_id: str) -> Optional[dict]:
    with psycopg2.connect(DATABASE_URL) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT session_id, collected_data, current_question, current_node
            FROM sessions
            WHERE session_id = %s
            """,
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

init_db()