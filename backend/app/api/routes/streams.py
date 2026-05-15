from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.observability.event_store import execution_events

router = APIRouter()


@router.websocket("/executions/ws/{execution_id}")
async def execution_stream(websocket: WebSocket, execution_id: str) -> None:
    await websocket.accept()
    last_seen = 0
    await websocket.send_json({"type": "connected", "execution_id": execution_id})

    try:
        while True:
            events = execution_events.snapshot(execution_id)
            if len(events) > last_seen:
                for event in events[last_seen:]:
                    await websocket.send_json(
                        {
                            "type": event.type,
                            "execution_id": event.execution_id,
                            "payload": event.payload,
                        }
                    )
                last_seen = len(events)
            await asyncio.sleep(0.25)
    except WebSocketDisconnect:
        return
