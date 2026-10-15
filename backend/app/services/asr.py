"""Xunfei real-time speech transcription — WebSocket relay service."""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from urllib.parse import quote

import websockets

from app.config import settings

logger = logging.getLogger(__name__)

class XunfeiASR:
    """Connects to Xunfei RT-ASR, sends PCM frames, yields JSON results."""

    WS_URL = "wss://rtasr.xfyun.cn/v1/ws"
    HOST = "rtasr.xfyun.cn"

    def __init__(self):
        self.app_id = settings.xf_app_id
        self.api_key = settings.xf_api_key
        self.api_secret = settings.xf_api_secret

    def _build_auth_url(self) -> str:
        date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        signature_origin = (
            f"host: {self.HOST}\ndate: {date}\nGET /v1/ws HTTP/1.1"
        )
        signature = base64.b64encode(
            hmac.new(
                self.api_secret.encode(),
                signature_origin.encode(),
                hashlib.sha256,
            ).digest()
        ).decode()
        authorization = base64.b64encode(
            f"{self.api_key}:{signature}".encode()
        ).decode()
        return (
            f"{self.WS_URL}?"
            f"host={quote(self.HOST)}&"
            f"date={quote(date)}&"
            f"authorization={quote(authorization)}&"
            f"appid={self.app_id}"
        )

    async def relay(self, client_ws, on_end_callback=None):
        """Bidirectional relay between client browser and Xunfei ASR.

        - Receives binary PCM frames from client_ws → forwards to Xunfei
        - Receives JSON results from Xunfei → forwards to client_ws
        - Calls on_end_callback(transcript_text) when session completes
        """
        url = self._build_auth_url()
        full_transcript = []

        async with websockets.connect(url, ping_interval=30) as xf_ws:
            # Wait for Xunfei handshake
            handshake = await xf_ws.recv()
            await client_ws.send_text(handshake)  # forward to client

            if '"ok"' not in handshake:
                await client_ws.send_text(
                    json.dumps({"type": "error", "message": f"Xunfei handshake failed"})
                )
                return

            async def client_to_xunfei():
                """Forward audio from browser to Xunfei."""
                try:
                    while True:
                        data = await client_ws.receive()
                        if data["type"] == "websocket.disconnect":
                            break
                        if "bytes" in data:
                            await xf_ws.send(data["bytes"])
                        elif "text" in data:
                            msg = json.loads(data["text"])
                            if msg.get("type") == "end":
                                await xf_ws.send(json.dumps({"type": "end"}))
                                break
                except Exception:
                    logger.debug("WebSocket client-to-xunfei relay interrupted", exc_info=True)

            async def xunfei_to_client():
                """Forward results from Xunfei to browser."""
                nonlocal full_transcript
                try:
                    while True:
                        msg = await xf_ws.recv()
                        await client_ws.send_text(msg)
                        data = json.loads(msg)
                        # Collect transcript text from result segments
                        if data.get("type") == "result":
                            text = data.get("text", "")
                            if text:
                                full_transcript.append(text)
                            if data.get("status") == "2":
                                break
                except Exception:
                    logger.debug("WebSocket xunfei-to-client relay interrupted", exc_info=True)

            await asyncio.gather(client_to_xunfei(), xunfei_to_client())

        if on_end_callback:
            await on_end_callback("".join(full_transcript))
