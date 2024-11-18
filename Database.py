import sqlite3
import uuid
from typing import Tuple, List, Dict, Optional

class Database:
    __instance = None
    DB_PATH = "./database.sqlite"

    @staticmethod
    def get_instance():
        if Database.__instance is None:
            Database()
        return Database.__instance

    def __init__(self):
        if Database.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Database.__instance = self
            self.conn = sqlite3.connect(Database.DB_PATH)
            self.cursor = self.conn.cursor()
            self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ship_providers (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                NAME TEXT UNIQUE NOT NULL,
                URL TEXT
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS shipments (
                ID TEXT PRIMARY KEY,
                CODE TEXT NOT NULL,
                PROVIDER_ID INTEGER NOT NULL,
                STATUS INTEGER NOT NULL,
                FOREIGN KEY (PROVIDER_ID) REFERENCES ship_providers(ID)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS current_tracking (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                SHIPMENT_ID TEXT NOT NULL UNIQUE,
                FOREIGN KEY (SHIPMENT_ID) REFERENCES shipments(ID)
            )
        """)
        self.conn.commit()

    def add_ship_provider(self, name: str, url: str = None) -> int:
        try:
            self.cursor.execute("INSERT INTO ship_providers (NAME, URL) VALUES (?, ?)", (name, url))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"Ship provider '{name}' already exists.")
            return None
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def get_provider_id(self, provider_name: str) -> Optional[int]:
        self.cursor.execute("SELECT ID FROM ship_providers WHERE NAME = ?", (provider_name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_all_providers(self) -> List[Tuple[int, str, str]]:
        self.cursor.execute("SELECT * FROM ship_providers")
        return self.cursor.fetchall()

    def insert_shipment(self, code: str, provider_name: str, is_delivered: bool = False) -> str:
        provider_id = self.get_provider_id(provider_name)
        if provider_id is None:
            raise ValueError(f"Provider '{provider_name}' not found.")
        shipment_id = str(uuid.uuid4())
        status = 1 if is_delivered else 0
        self.cursor.execute("INSERT INTO shipments (ID, CODE, PROVIDER_ID, STATUS) VALUES (?, ?, ?, ?)",
                            (shipment_id, code, provider_id, status))
        self.conn.commit()
        return shipment_id

    def update_shipment_status(self, shipment_id: str, is_delivered: bool) -> bool:
        try:
            status = 1 if is_delivered else 0
            self.cursor.execute("UPDATE shipments SET STATUS = ? WHERE ID = ?", (status, shipment_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error during update: {e}")
            return False

    def get_shipment(self, input_id_or_code: str) -> Optional[Tuple[str, str, int, bool]]:
        try:
            # Attempt to retrieve by ID first
            self.cursor.execute("SELECT * FROM shipments WHERE ID = ?", (input_id_or_code,))
            row = self.cursor.fetchone()
            if row:
                return row[0], row[1], row[2], bool(row[3])

            # If not found by ID, try retrieving by CODE
            self.cursor.execute("SELECT * FROM shipments WHERE CODE = ?", (input_id_or_code,))
            row = self.cursor.fetchone()
            if row:
                return row[0], row[1], row[2], bool(row[3])

            return None  # Not found by ID or CODE

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def get_all_shipments(self) -> List[Tuple[str, str, int, bool]]:
        self.cursor.execute("SELECT * FROM shipments")
        rows = self.cursor.fetchall()
        return [(row[0], row[1], row[2], bool(row[3])) for row in rows]
    
    def get_all_ongoing_shipments(self) -> List[Tuple[str, str, int, bool]]:
        self.cursor.execute("SELECT * FROM shipments WHERE status = 0")
        rows = self.cursor.fetchall()
        return [(row[0], row[1], row[2], bool(row[3])) for row in rows]
    
    def add_to_current_tracking(self, shipment_id: str) -> bool:
        """Adds a shipment to current_tracking, but only if the shipment exists in the shipments table.

        Args:
            shipment_id: The ID of the shipment to add.

        Returns:
            True if the shipment was added or already exists, False if the shipment ID is not found in the shipments table.
        """
        try:
            self.cursor.execute("SELECT 1 FROM shipments WHERE ID = ?", (shipment_id,))
            if self.cursor.fetchone():  # Check if shipment exists
                try:
                    self.cursor.execute("INSERT INTO current_tracking (SHIPMENT_ID) VALUES (?)", (shipment_id,))
                    self.conn.commit()
                    return True
                except sqlite3.IntegrityError:
                    print(f"Shipment '{shipment_id}' already in current_tracking.")
                    return True  # Already in tracking, consider this a success
                except sqlite3.Error as e:
                    print(f"Database error adding to current_tracking: {e}")
                    return False
            else:
                print(f"Shipment '{shipment_id}' not found in shipments table.")
                return False
        except sqlite3.Error as e:
            print(f"Database error checking shipment existence: {e}")
            return False

    def remove_from_current_tracking(self, shipment_id: str) -> bool:
        try:
            self.cursor.execute("DELETE FROM current_tracking WHERE SHIPMENT_ID = ?", (shipment_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def get_current_tracking(self) -> List[Tuple[int, str]]:
        self.cursor.execute("SELECT * FROM current_tracking")
        return self.cursor.fetchall()

    def update_shipment_status(self, shipment_id: str, status: str) -> bool:
        try:
            self.cursor.execute("UPDATE shipments SET STATUS = ? WHERE ID = ?", (status, shipment_id))
            self.conn.commit()
            if status == "Delivered":
                self.remove_from_current_tracking(shipment_id)
            return True
        except sqlite3.Error as e:
            print(f"Database error during update: {e}")
            return False

    def close(self):
        self.conn.close()
