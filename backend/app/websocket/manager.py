from fastapi import WebSocket
import structlog

logger = structlog.get_logger()


class ConnectionManager:

    def __init__(self):
        self.connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, org_id: int):
        await websocket.accept()
        if org_id not in self.connections:
            self.connections[org_id] = []
        self.connections[org_id].append(websocket)
        logger.info("ws_connected", org_id=org_id, total=len(self.connections[org_id]))

    def disconnect(self, websocket: WebSocket, org_id: int):
        if org_id in self.connections:
            self.connections[org_id].discard(websocket) if hasattr(
                self.connections[org_id], 'discard'
            ) else None
            try:
                self.connections[org_id].remove(websocket)
            except ValueError:
                pass
            if not self.connections[org_id]:
                del self.connections[org_id]
        logger.info("ws_disconnected", org_id=org_id)

    async def broadcast_to_org(self, org_id: int, message: dict):
        if org_id not in self.connections:
            return

        dead = []
        for ws in self.connections[org_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)

        # Clean up dead connections
        for ws in dead:
            self.disconnect(ws, org_id)

    async def broadcast_alert(self, org_id: int, alert_data: dict):
        await self.broadcast_to_org(org_id, {
            "type": "alert_triggered",
            "data": alert_data,
        })

    async def broadcast_new_event(self, org_id: int, event_data: dict):
        await self.broadcast_to_org(org_id, {
            "type": "new_event",
            "data": event_data,
        })


# Singleton instance shared across the app
ws_manager = ConnectionManager()
