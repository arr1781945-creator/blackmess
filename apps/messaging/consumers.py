"""
apps/messaging/consumers.py

FIX #1 — Hapus duplikasi kode (dua versi ChatConsumer dalam satu file)
  File sebelumnya berisi versi lama corrupted + versi baru. Dibersihkan.

FIX #2 — Pakai self.scope['user'] dari JWTAuthMiddlewareStack
  Sebelumnya consumer re-implement JWT auth sendiri dengan manual
  query string parsing yang:
  - Tidak handle URL encoding (%3D, dll)
  - Tidak cek token blacklist
  - Tidak cek mfa_verified
  JWTAuthMiddlewareStack sudah handle semua ini. Consumer cukup
  baca dari self.scope['user'].

FIX #3 — user dan avatar dari scope['user'], bukan dari client payload
  Sebelumnya: user = data.get('user', 'Anonym') — bisa impersonate siapapun
  Sekarang: user diambil dari token yang sudah terverifikasi.

FIX #4 — Size limit pada message payload
  Tambah MAX_MESSAGE_SIZE untuk cegah DoS via payload besar.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

# Maksimum ukuran payload pesan — 64KB cukup untuk pesan E2EE
MAX_MESSAGE_SIZE = 64 * 1024  # 64 KB


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.channel_name_slug = self.scope['url_route']['kwargs']['channel_name']
        self.room_group_name = f'chat_{self.channel_name_slug}'

        # FIX #2: Gunakan user dari JWTAuthMiddlewareStack
        # Middleware sudah handle: JWT parse, blacklist check, is_active check
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            logger.warning(
                "WS connect rejected — unauthenticated. channel=%s",
                self.channel_name_slug,
            )
            await self.close(code=4001)
            return

        self.authenticated_user = user
        self.authenticated_username = user.username

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()
        logger.info(
            "WS connected: user=%s channel=%s",
            user.username, self.channel_name_slug,
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )
        logger.info(
            "WS disconnected: user=%s channel=%s code=%s",
            getattr(self, 'authenticated_username', 'unknown'),
            self.channel_name_slug,
            close_code,
        )

    async def receive(self, text_data):
        # FIX #4: Size limit — cegah DoS
        if len(text_data) > MAX_MESSAGE_SIZE:
            logger.warning(
                "WS payload terlalu besar: %d bytes user=%s",
                len(text_data), getattr(self, 'authenticated_username', 'unknown'),
            )
            await self.close(code=4002)
            return

        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, ValueError):
            logger.warning("WS invalid JSON dari user=%s", getattr(self, 'authenticated_username', 'unknown'))
            return

        # FIX #3: user dan avatar dari scope['user'] yang terautentikasi
        # Bukan dari payload client yang bisa di-manipulasi
        user = self.authenticated_user
        username = self.authenticated_username
        avatar = getattr(user, 'avatar_ipfs_cid', '?') or '?'

        from django.utils import timezone
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': data.get('message', ''),
                'ciphertext_b64': data.get('ciphertext_b64', ''),  # E2EE payload
                'nonce_b64': data.get('nonce_b64', ''),
                'auth_tag_b64': data.get('auth_tag_b64', ''),
                'user': username,                   # FIX #3: dari auth, bukan client
                'avatar': avatar,                   # FIX #3: dari auth, bukan client
                'time': timezone.now().strftime('%I:%M %p'),
                'id': data.get('id', ''),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event.get('message', ''),
            'ciphertext_b64': event.get('ciphertext_b64', ''),
            'nonce_b64': event.get('nonce_b64', ''),
            'auth_tag_b64': event.get('auth_tag_b64', ''),
            'user': event['user'],
            'avatar': event['avatar'],
            'time': event['time'],
            'id': event['id'],
        }))
