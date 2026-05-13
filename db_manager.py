import sqlite3
import json
import datetime
import os

class DBManager:
    def __init__(self, db_path="game_data.db"):
        self.db_path = db_path
        self.connected = False
        try:
            self._init_db()
            self.connected = True
        except Exception as e:
            print(f"SQLite connection failed: {e}")

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Saved Games Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS saved_games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    player_name TEXT,
                    board_json TEXT,
                    turn TEXT,
                    scores_json TEXT,
                    ai_memory_json TEXT,
                    timestamp DATETIME
                )
            ''')
            # Game History Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT,
                    winner TEXT,
                    player_score INTEGER,
                    ai_score INTEGER,
                    moves INTEGER,
                    duration INTEGER,
                    date DATETIME
                )
            ''')
            conn.commit()

    def save_game(self, name, board_state, turn, scores, ai_memory, player_name):
        if not self.connected: return False
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Use JSON to store complex structures
                board_json = json.dumps(board_state)
                scores_json = json.dumps(scores)
                ai_memory_json = json.dumps(ai_memory)
                timestamp = datetime.datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO saved_games 
                    (name, player_name, board_json, turn, scores_json, ai_memory_json, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, player_name, board_json, turn, scores_json, ai_memory_json, timestamp))
                conn.commit()
            return True
        except Exception as e:
            print(f"Save failed: {e}")
            return False

    def load_game(self, save_id):
        if not self.connected: return None
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM saved_games WHERE id = ?", (save_id,))
                row = cursor.fetchone()
                if row:
                    res = dict(row)
                    # Convert JSON back to Python objects
                    res["board"] = json.loads(res["board_json"])
                    res["scores"] = json.loads(res["scores_json"])
                    res["ai_memory"] = json.loads(res["ai_memory_json"])
                    return res
            return None
        except Exception as e:
            print(f"Load failed: {e}")
            return None

    def get_saved_games(self):
        if not self.connected: return []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT *, id as _id FROM saved_games ORDER BY timestamp DESC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Fetch saves failed: {e}")
            return []

    def delete_save(self, save_id):
        if not self.connected: return False
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM saved_games WHERE id = ?", (save_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Delete failed: {e}")
            return False

    def add_to_history(self, winner, player_score, ai_score, moves, duration, player_name):
        if not self.connected: return False
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                date = datetime.datetime.now().isoformat()
                cursor.execute('''
                    INSERT INTO game_history 
                    (player_name, winner, player_score, ai_score, moves, duration, date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (player_name, winner, player_score, ai_score, moves, duration, date))
                conn.commit()
            return True
        except Exception as e:
            print(f"History save failed: {e}")
            return False

    def get_game_history(self):
        if not self.connected: return []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM game_history ORDER BY date DESC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Fetch history failed: {e}")
            return []
