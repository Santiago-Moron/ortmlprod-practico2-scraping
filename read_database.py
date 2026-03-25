
from src.database.database_connection import get_connection, show_all

if __name__ == "__main__":
   conn = get_connection()
   show_all()
   conn.close()