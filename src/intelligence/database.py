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
            # Converts query results from tuples to dictionary objects
            self.conn.row_factory = sqlite3.Row

        return self.conn
    
        
    def _init_db(self):
        self._get_connection()  # Ensure connection is established
        self._create_sessions_table()
        self._create_user_stats_table()
        self._create_events_table()
        self._create_achievements_table()


    def _create_sessions_table(self):
        cursor = self.conn.cursor()
        
        # Create a SESSIONS table to store user session data
        # id - identifier for each session
        # start_time - the time at which the session started
        # end_time - the time at which the session ended
        # duration - the total duration of the session in seconds
        # events - the total number of events (distractions / look aways) during the session
        # time_away - the total time spent away from the screen during the session in seconds
        # look_away_time - the total time spent looking away from the screen during the session in seconds
        # distraction_time - the total time spent distracted during the session in seconds

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS SESSIONS(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration INTEGER,
            events INTEGER DEFAULT 0,
            time_away INTEGER DEFAULT 0,
            look_away_time INTEGER DEFAULT 0,
            distraction_time INTEGER DEFAULT 0
            )
            '''
        )
        self.conn.commit()


    def _create_user_stats_table(self):
        cursor = self.conn.cursor()
        
        
        # Create a USER_STATS table to store overall user statistics
        # avg_focus_time - the average focus time per session in seconds
        # total_sessions - the total number of sessions
        # total_time_spent - the total time spent in sessions in seconds
        # number_of_coins - the total number of coins earned by the user
        # exp - the total experience points earned by the user
        # total_distractions - the total number of distractions across all sessions
        # total_look_aways - the total number of look aways across all sessions

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS USER_STATS(
            avg_focus_time REAL DEFAULT 0.0,
            total_sessions INTEGER DEFAULT 0,
            total_time_spent INTEGER DEFAULT 0,
            number_of_coins INTEGER DEFAULT 0,
            exp INTEGER DEFAULT 0,
            total_distractions INTEGER DEFAULT 0,
            total_look_aways INTEGER DEFAULT 0
            )
            '''
        )
        self.conn.commit()

    def _create_events_table(self):
        cursor = self.conn.cursor()
        
        # Create an EVENTS table to events (distractions / look aways) during sessions
        # id - identifier for each event
        # session_id - the session during which the event occurred
        # total_distractions - the total number of distractions during the session
        # total_look_aways - the total number of look aways during the session
        # event_type - the type of event (distraction or look away)
        # timestamp - the time at which the event occurred
        # duration - the duration of the event

        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS EVENTS(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES SESSIONS(id),
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            duration INTEGER
            )
            '''
        )
        self.conn.commit()

    # Idea of variables for the achievements table - can be expanded/changed later
    def _create_achievements_table(self):
        cursor = self.conn.cursor()
        
        # Create an ACHIEVEMENTS table to store user achievements
        # id - identifier for each achievement
        # name - the name of the achievement
        # description - a description of the achievement
        # criteria - the criteria for earning the achievement (e.g., "Focus for 1 hour straight")
        # earned - a boolean indicating whether the achievement has been earned
        # earned_at - the time at which the achievement was earned
        
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS ACHIEVEMENTS(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            criteria TEXT NOT NULL,
            earned BOOLEAN DEFAULT 0,
            earned_at TEXT
            )
            '''
        )
        self.conn.commit()
