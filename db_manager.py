import pymongo
from bson import ObjectId
import datetime

class DBManager:
    def __init__(self, uri="mongodb://localhost:27017/"):
        try:
            self.client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=2000)
            self.db = self.client["color_memory_chess"]
            self.saves = self.db["saved_games"]
            self.history = self.db["game_history"]
            # Test connection
            self.client.server_info()
            self.connected = True
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            self.connected = False

    def save_game(self, name, board_state, turn, scores, ai_memory, player_name):
        if not self.connected: return False
        data = {
            "name": name,
            "player": player_name,
            "board": board_state,
            "turn": turn,
            "scores": scores,
            "ai_memory": ai_memory,
            "timestamp": datetime.datetime.now()
        }
        self.saves.update_one({"name": name}, {"$set": data}, upsert=True)
        return True

    def load_game(self, save_id):
        if not self.connected: return None
        return self.saves.find_one({"_id": ObjectId(save_id)})

    def get_saved_games(self):
        if not self.connected: return []
        return list(self.saves.find().sort("timestamp", -1))

    def delete_save(self, save_id):
        if not self.connected: return False
        self.saves.delete_one({"_id": ObjectId(save_id)})
        return True

    def add_to_history(self, winner, player_score, ai_score, moves, duration, player_name):
        if not self.connected: return False
        data = {
            "player": player_name,
            "winner": winner,
            "score": {"player": player_score, "ai": ai_score},
            "moves": moves,
            "duration": duration,
            "date": datetime.datetime.now()
        }
        self.history.insert_one(data)
        return True

    def get_game_history(self):
        if not self.connected: return []
        return list(self.history.find().sort("date", -1))
