"""WebSocket-based inference service connection manager.

Each local inference service (ltx2, whisper, …) connects to aideo-serv
via WebSocket at startup.  The manager tracks active connections and
routes task_submit / task_cancel messages to the correct service.
"""

import asyncio
import logging
from uuid import UUID

from fastapi import WebSocket

from aideo_serv.models.events import InferenceMessage, InferenceRegistration, TaskType

logger = logging.getLogger(__name__)


class InferenceServiceManager:
    """Tracks connected inference services and routes messages to them.

    Each service is identified by its ``service_type`` (e.g. "ltx2", "whisper").
    Only one instance of each service type may be connected at a time.
    """

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}
        self._capabilities: dict[str, list[TaskType]] = {}
        self._pending_tasks: dict[str, asyncio.Task] = {}

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def handle_connection(self, websocket: WebSocket) -> None:
        """Manage a single inference-service WebSocket connection.

        Waits for a ``register`` message, records the service, then
        loops forever receiving messages and dispatching them to
        :meth:`_handle_message`.  On disconnect the service is
        unregistered automatically.
        """
        await websocket.accept()
        service_type: str | None = None

        try:
            # ---- registration handshake ---------------------------------
            raw = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
            reg = InferenceRegistration.model_validate(raw)
            service_type = reg.service_type

            # Displace any previous connection of the same type
            old = self._connections.pop(service_type, None)
            if old is not None:
                logger.warning(
                    "Replacing existing %s inference connection", service_type
                )
                try:
                    await old.close(code=4001, reason="Superseded")
                except Exception:
                    pass

            self._connections[service_type] = websocket
            self._capabilities[service_type] = reg.capabilities

            logger.info(
                "Inference service registered: type=%s capabilities=%s version=%s",
                service_type,
                reg.capabilities,
                reg.version,
            )

            # Tell the service it's registered
            await websocket.send_json(
                InferenceMessage(
                    type="registered",
                    data={"service_type": service_type},
                ).model_dump(mode="json")
            )

            # ---- message loop -------------------------------------------
            while True:
                raw = await websocket.receive_json()
                await self._handle_message(service_type, raw)

        except asyncio.TimeoutError:
            logger.warning(
                "Inference service %s did not register within 30 s", service_type
            )
        except Exception:
            logger.debug("Inference service %s disconnected", service_type)
        finally:
            if service_type is not None:
                self._connections.pop(service_type, None)
                self._capabilities.pop(service_type, None)
                logger.info("Inference service unregistered: type=%s", service_type)

    # ------------------------------------------------------------------
    # Outgoing (aideo-serv → inference service)
    # ------------------------------------------------------------------

    async def send_to_service(
        self, service_type: str, message: InferenceMessage
    ) -> None:
        """Send a message to a connected inference service."""
        ws = self._connections.get(service_type)
        if ws is None:
            raise LookupError(
                f"Inference service '{service_type}' is not connected"
            )
        await ws.send_json(message.model_dump(mode="json"))

    def is_connected(self, service_type: str) -> bool:
        """Return True if an inference service of the given type is connected."""
        return service_type in self._connections

    def is_any_connected(self) -> bool:
        """Return True if at least one inference service is connected."""
        return len(self._connections) > 0

    def get_capabilities(self, service_type: str) -> list[TaskType]:
        """Return the capabilities advertised by a connected service."""
        return self._capabilities.get(service_type, [])

    # ------------------------------------------------------------------
    # Incoming (inference service → aideo-serv)
    # ------------------------------------------------------------------

    async def _handle_message(
        self, service_type: str, raw: dict
    ) -> None:
        """Dispatch an incoming message from an inference service.

        Progress / completed / error / cancelled events are forwarded
        to the TaskService so they reach the client-facing WebSocket.
        """
        from aideo_serv.dependencies import get_task_service

        msg = InferenceMessage.model_validate(raw)
        svc = get_task_service()

        if msg.task_id is None:
            logger.warning("Message without task_id from %s: %s", service_type, msg.type)
            return

        task_id = UUID(msg.task_id)

        try:
            if msg.type == "progress":
                progress = float(msg.data.get("progress", 0))
                message = str(msg.data.get("message", ""))
                svc.update_progress(task_id, progress, message)
            elif msg.type == "completed":
                result_path = str(msg.data.get("result_path", ""))
                result_data = msg.data.get("result_data")
                svc.complete(task_id, result_path, result_data)
            elif msg.type == "error":
                message = str(msg.data.get("message", "Unknown error"))
                svc.fail(task_id, message)
            elif msg.type == "cancelled":
                pass  # Already handled locally
        except ValueError:
            logger.debug(
                "Message %s for task %s ignored (already terminal)", msg.type, task_id
            )


# ------------------------------------------------------------------
# Singleton
# ------------------------------------------------------------------

_mgr: InferenceServiceManager | None = None


def get_inference_manager() -> InferenceServiceManager:
    """Return the global InferenceServiceManager singleton."""
    global _mgr
    if _mgr is None:
        _mgr = InferenceServiceManager()
    return _mgr


def set_inference_manager(mgr: InferenceServiceManager) -> None:
    """Replace the global singleton (for testing)."""
    global _mgr
    _mgr = mgr
