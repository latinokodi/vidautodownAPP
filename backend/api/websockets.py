from typing import List
from fastapi import WebSocket
import logging

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info(f"Client connected. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logging.info(f"Client disconnected. Active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        # Broadcast to all connected clients
        # Iterate over a copy in case of disconnection during iteration
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                # If send fails, assume disconnected
                self.disconnect(connection)

manager = ConnectionManager()
