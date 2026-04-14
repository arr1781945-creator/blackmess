"""
apps/vault/views.py — KYC + Blob endpoints

FIX — BlobStoreViewSet: permission_classes didefinisikan dua kali
  Python menggunakan definisi terakhir. Hapus definisi pertama yang
  salah agar tidak menyesatkan developer.
"""
import logging
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.users.permissions import IsMFAVerified
from .models import UserKYCVault, EncryptedBlobStore
from .serializers import KYCVaultReadSerializer, EncryptedBlobSerializer
from .permissions import RequiresVaultSession

logger = logging.getLogger(__name__)


class KYCVaultViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsMFAVerified, RequiresVaultSession]

    @action(detail=False, methods=["get"])
    def my_kyc(self, request):
        try:
            record = UserKYCVault.objects.get(user=request.user)
        except UserKYCVault.DoesNotExist:
            return Response({"detail": "No KYC record found."}, status=404)
        return Response(KYCVaultReadSerializer(record).data)

    @action(detail=False, methods=["post"])
    def submit_kyc(self, request):
        """Submit KYC data — fields must be pre-encrypted by client."""
        if UserKYCVault.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "KYC record already exists. Use PATCH to update."},
                status=400,
            )
        required = [
            "full_name_enc", "date_of_birth_enc", "id_type",
            "id_number_enc", "id_expiry_enc",
        ]
        for field in required:
            if not request.data.get(field):
                return Response({"detail": f"Field required: {field}"}, status=400)

        record = UserKYCVault.objects.create(
            user=request.user,
            **{k: request.data[k] for k in required},
        )
        return Response(KYCVaultReadSerializer(record).data, status=201)


class BlobStoreViewSet(viewsets.ModelViewSet):
    # FIX: Hanya satu definisi permission_classes — yang benar
    # Sebelumnya ada dua definisi, yang pertama (IsAuthenticated saja)
    # di-override oleh yang kedua. Dihapus untuk menghindari kebingungan.
    permission_classes = [IsAuthenticated, IsMFAVerified, RequiresVaultSession]
    serializer_class = EncryptedBlobSerializer

    def get_queryset(self):
        return EncryptedBlobStore.objects.filter(
            owner=self.request.user,
            is_destroyed=False,
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
