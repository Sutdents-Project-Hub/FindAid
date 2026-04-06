import sqlite3


def get_connection(database_file):
    conn = sqlite3.connect(database_file, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn):
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS resources (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            audience_tags TEXT,
            description TEXT,
            address TEXT,
            lat REAL,
            lng REAL,
            phone TEXT,
            url TEXT,
            hours TEXT,
            eligibility TEXT,
            apply_steps TEXT,
            source_name TEXT,
            source_url TEXT,
            source_license TEXT,
            updated_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS action_plans (
            plan_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            need_category TEXT,
            user_context TEXT,
            steps TEXT,
            materials TEXT,
            linked_resource_ids TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()

