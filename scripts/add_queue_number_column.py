import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'mediqueue.db')

def add_column():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(queue_entries)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'queue_number' in columns:
            print("Column 'queue_number' already exists in 'queue_entries' table.")
        else:
            print("Adding 'queue_number' column to 'queue_entries' table...")
            cursor.execute("ALTER TABLE queue_entries ADD COLUMN queue_number INTEGER")
            conn.commit()
            print("Column added successfully.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_column()
