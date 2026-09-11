import sqlite3
from pathlib import Path


DB_PATH = (
    Path(__file__).resolve().parent
    / "database"
    / "devops_assistant.db"
)


def main():

    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return

    connection = sqlite3.connect(DB_PATH)

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                approval_id TEXT,
                action TEXT NOT NULL,
                tool TEXT NOT NULL,
                arguments TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL,
                result TEXT,
                created_at DATETIME
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_audit_logs_project_id
            ON audit_logs(project_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_audit_logs_approval_id
            ON audit_logs(approval_id)
            """
        )

        connection.commit()

        print("✅ Audit log table created successfully.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()