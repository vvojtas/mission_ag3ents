"""Fire-and-forget WebSocket client for the dashboard.

Sends ``common.events.Event`` payloads (serialised as JSON) to the dashboard
WebSocket without blocking callers on network I/O.

Usage::

    async with DashboardClient(settings.dashboard_ws_url) as dc:
        dc.post(events.ConversationStart())
        dc.post(events.LLMRequest(messages=history))

Implements ``common.events.EventPoster``.
"""

from __future__ import annotations

import asyncio
import contextlib
from types import TracebackType

import websockets
from websockets.exceptions import WebSocketException

from common.events import Event, EventPoster
from common.logging_config import get_logger
from dashboard.event_map import serialize_event

logger = get_logger(__name__)


class DashboardClient:
    """Queue-backed sender to the dashboard WebSocket.

    Use as an async context manager so a background task drains the queue.
    ``post`` returns immediately after enqueueing; it does not await network I/O.
    If the server is unavailable, errors are logged at most once per outage
    (until a send succeeds again, resetting the flag).

    Implements ``common.events.EventPoster``.

    Args:
        url: WebSocket URL of the dashboard endpoint.
        open_timeout_s: Seconds to wait for a connection before retrying.
        retry_delay_s: Seconds to wait between reconnection attempts.
    """

    def __init__(
        self,
        url: str,
        *,
        open_timeout_s: float = 10.0,
        retry_delay_s: float = 0.05,
    ) -> None:
        self._url = url
        self._open_timeout_s = open_timeout_s
        self._retry_delay_s = retry_delay_s
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker: asyncio.Task[None] | None = None
        self._logged_unreachable = False

    async def __aenter__(self) -> DashboardClient:
        self._worker = asyncio.create_task(
            self._run_worker(), name="dashboard_ws"
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._worker is None:
            return
        self._worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._worker
        self._worker = None

    def post(self, event: Event) -> None:
        """Enqueue an event for async delivery to the dashboard WebSocket.

        Returns immediately; delivery happens in a background task.

        Args:
            event: Any ``common.events.Event`` variant.
        """
        if self._worker is None:
            logger.debug("Dashboard client not started; dropping event")
            return
        self._queue.put_nowait(serialize_event(event))

    def _mark_recovered(self) -> None:
        self._logged_unreachable = False

    def _maybe_log_unreachable(self, exc: BaseException) -> None:
        if self._logged_unreachable:
            return
        logger.error("Dashboard unreachable (%s): %s", self._url, exc)
        self._logged_unreachable = True

    async def _transmit_until_sent(
        self,
        item: str,
        ws: websockets.ClientConnection | None,
    ) -> websockets.ClientConnection | None:
        """Send one queued JSON string, reconnecting until success or cancellation."""
        sent = False
        while not sent:
            if ws is None:
                try:
                    ws = await asyncio.wait_for(
                        websockets.connect(self._url),
                        timeout=self._open_timeout_s,
                    )
                except asyncio.CancelledError:
                    raise
                except (OSError, WebSocketException) as exc:
                    self._maybe_log_unreachable(exc)
                    await asyncio.sleep(self._retry_delay_s)
                    continue
                self._mark_recovered()

            try:
                await ws.send(item)
                sent = True
            except asyncio.CancelledError:
                raise
            except (OSError, WebSocketException) as exc:
                self._maybe_log_unreachable(exc)
                with contextlib.suppress(OSError, WebSocketException):
                    await ws.close()
                ws = None
        return ws

    async def _run_worker(self) -> None:
        ws: websockets.ClientConnection | None = None
        try:
            while True:
                item = await self._queue.get()
                assert isinstance(item, str)
                ws = await self._transmit_until_sent(item, ws)
        finally:
            if ws is not None:
                with contextlib.suppress(OSError, WebSocketException):
                    await ws.close()

