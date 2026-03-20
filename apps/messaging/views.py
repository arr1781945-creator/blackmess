"""
apps/messaging/views.py
Message REST API — ZK server never decrypts, IPFS attachments.
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import Message, Thread, Attachment
from .serializers import MessageSerializer, ThreadSerializer
from .ipfs_handler import upload_encrypted_file as upload_to_ipfs
import logging

logger = logging.getLogger(__name__)


class MessageListView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        channel_id = self.kwargs["channel_id"]
        return Message.objects.filter(
            channel_id=channel_id,
            is_deleted=False
        ).order_by("created_at").select_related("sender", "thread")

    def perform_create(self, serializer):
        # ZK: server stores only ciphertext, never plaintext
        serializer.save(
            sender=self.request.user,
            channel_id=self.kwargs["channel_id"]
        )


class MessageDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Message.objects.all()

    def destroy(self, request, *args, **kwargs):
        msg = self.get_object()
        if msg.sender != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        # DoD wipe before delete
        msg.ciphertext_b64 = ""
        msg.nonce_b64 = ""
        msg.auth_tag_b64 = ""
        msg.is_deleted = True
        msg.save()
        msg.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AttachmentUploadView(APIView):
    """Upload file to IPFS — returns CID."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, channel_id):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file"}, status=400)
        try:
            cid = upload_to_ipfs(file.read(), file.name)
            attachment = Attachment.objects.create(
                uploaded_by=request.user,
                channel_id=channel_id,
                filename=file.name,
                ipfs_cid=cid,
                file_size=file.size,
            )
            return Response({"cid": cid, "id": str(attachment.id)}, status=201)
        except Exception as e:
            logger.error("IPFS upload failed: %s", e)
            return Response({"error": "Upload failed"}, status=500)


class ThreadListView(generics.ListCreateAPIView):
    serializer_class = ThreadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Thread.objects.filter(
            channel_id=self.kwargs["channel_id"]
        ).order_by("-last_reply_at")

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .tasks import schedule_message_deletion

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_self_destruct(request, message_id):
    seconds = request.data.get('seconds', 300)  # default 5 menit
    schedule_message_deletion.delay(str(message_id), int(seconds))
    return Response({'message': f'Pesan akan terhapus dalam {seconds} detik'})
