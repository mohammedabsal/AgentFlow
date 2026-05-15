"""
WebSocket manager for real-time execution streaming.

Handles:
- Live agent updates
- Code generation streaming
- Execution logs
- Status updates
- Error notifications
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Optional
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect

from app.orchestration.contracts import ExecutionStreamMessage

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections for real-time streaming."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.subscriptions: dict[str, set[str]] = {}  # execution_id -> connection_ids

    async def connect(self, execution_id: str, websocket: WebSocket) -> str:
        """Register a new WebSocket connection."""
        await websocket.accept()

        connection_id = str(uuid4())

        if execution_id not in self.active_connections:
            self.active_connections[execution_id] = []
            self.subscriptions[execution_id] = set()

        self.active_connections[execution_id].append(websocket)
        self.subscriptions[execution_id].add(connection_id)

        logger.info(f"WebSocket connected: {connection_id} for execution {execution_id}")
        return connection_id

    async def disconnect(self, execution_id: str, connection_id: str) -> None:
        """Unregister a WebSocket connection."""
        if execution_id in self.subscriptions:
            self.subscriptions[execution_id].discard(connection_id)

        if execution_id in self.active_connections:
            if not self.active_connections[execution_id]:
                del self.active_connections[execution_id]
                del self.subscriptions[execution_id]

        logger.info(f"WebSocket disconnected: {connection_id} from execution {execution_id}")

    async def broadcast(self, execution_id: str, message: ExecutionStreamMessage) -> None:
        """Broadcast message to all subscribers of an execution."""
        if execution_id not in self.active_connections:
            return

        disconnected = []
        for websocket in self.active_connections[execution_id]:
            try:
                await websocket.send_json(message.model_dump())
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.append(websocket)

        # Clean up disconnected websockets
        for ws in disconnected:
            try:
                self.active_connections[execution_id].remove(ws)
            except ValueError:
                pass

    async def send_log(
        self,
        execution_id: str,
        message: str,
        level: str = "info",
        source: str = "system",
    ) -> None:
        """Send a log message."""
        stream_msg = ExecutionStreamMessage(
            type="log",
            execution_id=execution_id,
            content=message,
            metadata={"level": level, "source": source},
        )
        await self.broadcast(execution_id, stream_msg)

    async def send_status(
        self,
        execution_id: str,
        status: str,
        details: Optional[dict] = None,
    ) -> None:
        """Send status update."""
        stream_msg = ExecutionStreamMessage(
            type="status",
            execution_id=execution_id,
            content=status,
            metadata=details or {},
        )
        await self.broadcast(execution_id, stream_msg)

    async def send_artifact(
        self,
        execution_id: str,
        artifact_id: str,
        path: str,
        content: Optional[str] = None,
    ) -> None:
        """Send artifact generation update."""
        stream_msg = ExecutionStreamMessage(
            type="artifact",
            execution_id=execution_id,
            content=f"Generated: {path}",
            metadata={"artifact_id": artifact_id, "path": path, "preview": content[:200] if content else None},
        )
        await self.broadcast(execution_id, stream_msg)

    async def send_progress(
        self,
        execution_id: str,
        completed: int,
        total: int,
        current_task: Optional[str] = None,
    ) -> None:
        """Send progress update."""
        stream_msg = ExecutionStreamMessage(
            type="progress",
            execution_id=execution_id,
            content=f"Progress: {completed}/{total}",
            metadata={"completed": completed, "total": total, "current_task": current_task},
        )
        await self.broadcast(execution_id, stream_msg)

    async def send_error(
        self,
        execution_id: str,
        error_message: str,
        error_type: Optional[str] = None,
    ) -> None:
        """Send error notification."""
        stream_msg = ExecutionStreamMessage(
            type="error",
            execution_id=execution_id,
            content=error_message,
            metadata={"error_type": error_type or "unknown"},
        )
        await self.broadcast(execution_id, stream_msg)

    async def send_completion(
        self,
        execution_id: str,
        summary: str,
        success: bool,
    ) -> None:
        """Send completion message."""
        stream_msg = ExecutionStreamMessage(
            type="complete",
            execution_id=execution_id,
            content=summary,
            metadata={"success": success},
        )
        await self.broadcast(execution_id, stream_msg)

    def get_active_subscriptions(self) -> dict[str, int]:
        """Get count of active subscriptions per execution."""
        return {exec_id: len(subs) for exec_id, subs in self.subscriptions.items()}

    def is_active(self, execution_id: str) -> bool:
        """Check if execution has active subscribers."""
        return execution_id in self.active_connections and len(self.active_connections[execution_id]) > 0


# Global connection manager instance
connection_manager = ConnectionManager()


async def handle_execution_websocket(websocket: WebSocket, execution_id: str) -> None:
    """Handle WebSocket connection for execution streaming."""
    connection_id = await connection_manager.connect(execution_id, websocket)

    try:
        # Send initial connection message
        await websocket.send_json(
            {
                "type": "connected",
                "execution_id": execution_id,
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Keep connection alive and handle incoming messages
        while True:
            # Receive message (can be used for control messages)
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})

            elif data.get("type") == "subscribe":
                # Can subscribe to specific channels
                logger.info(f"Connection {connection_id} subscribed to {data.get('channel')}")

            elif data.get("type") == "unsubscribe":
                logger.info(f"Connection {connection_id} unsubscribed from {data.get('channel')}")

    except WebSocketDisconnect:
        await connection_manager.disconnect(execution_id, connection_id)
    except Exception as e:
        logger.error(f"WebSocket error for {execution_id}: {e}")
        await connection_manager.disconnect(execution_id, connection_id)
