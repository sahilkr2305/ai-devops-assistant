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
            "PRAGMA table_info(approval_requests)"
        )

        columns = {
            row[1]
            for row in cursor.fetchall()
        }

        if "project_id" in columns:

            print(
                "project_id already exists."
            )

        else:

            # Existing approvals are local development data.
            # Assign them to project 1 during migration.
            cursor.execute(
                """
                ALTER TABLE approval_requests
                ADD COLUMN project_id INTEGER
                NOT NULL DEFAULT 1
                """
            )

            print(
                "Added project_id to approval_requests."
            )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_approval_requests_project_id
            ON approval_requests(project_id)
            """
        )

        connection.commit()

        print(
            "✅ Approval project migration completed."
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()