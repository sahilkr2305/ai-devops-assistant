import sqlite3
from pathlib import Path


DB_PATH = (
    Path(__file__).resolve().parent
    / "database"
    / "devops_assistant.db"
)


NEW_COLUMNS = {
    "approved_at": "DATETIME",
    "executed_at": "DATETIME",
    "expires_at": "DATETIME",
}


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

        existing_columns = {
            row[1]
            for row in cursor.fetchall()
        }

        for column_name, column_type in NEW_COLUMNS.items():

            if column_name in existing_columns:
                print(
                    f"Already exists: {column_name}"
                )
                continue

            cursor.execute(
                f"""
                ALTER TABLE approval_requests
                ADD COLUMN {column_name} {column_type}
                """
            )

            print(
                f"Added column: {column_name}"
            )

        connection.commit()

        print("\n✅ Approval database migration completed.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()