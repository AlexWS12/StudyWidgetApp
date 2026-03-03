import sqlite3


#connection = sqlite3()

class Database:
    def __init__(self, db_path: str = "data.db"):
        self.db_path = db_path 
        self.conn = None
        self._init_db() # Created DB locally

# Protected method get_connection with return type sqlite3.Connection
    def _get_connection(self) -> sqlite3.Connection:
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            # Converts tuples and other objects into dictionary objects
            self.conn.row_factory = sqlite3.Row
        
    def _init_db(self):
        cursor = conn.cursor()
        conn = self._get_connection()
        
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS SESSONS(
            id INTEGER PRIMARY KEY AUTO INCREMENT,
            start_time TEXT NON NULL,
            end_time TEXT,
            distractions INTEGER DEFAULT 0, 
            )
            '''
        )
        conn.commit()
