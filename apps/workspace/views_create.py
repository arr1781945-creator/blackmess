"""Workspace creation — Slack-style dengan slug/URL unik."""
import re
from django.utils.text import slugify
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Workspace, WorkspaceMember
from apps.users.models import UserRole


def generate_slug(name: str) -> str:
    base = slugify(name)
    if not base:
        base = 'workspace'
    slug = base
    counter = 1
    while Workspace.objects.filter(slug=slug).exists():
        slug = f'{base}-{counter}'
        counter += 1
    return slug


class WorkspaceCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get('name', '').strip()
        custom_slug = request.data.get('slug', '').strip().lower()

        if not name:
            return Response({'detail': 'Nama workspace diperlukan.'}, status=400)

        if len(name) < 2 or len(name) > 64:
            return Response({'detail': 'Nama workspace harus 2-64 karakter.'}, status=400)

        # Validasi slug custom
        if custom_slug:
            if not re.match(r'^[a-z0-9-]+$', custom_slug):
                return Response({'detail': 'URL hanya boleh huruf kecil, angka, dan tanda -'}, status=400)
            if Workspace.objects.filter(slug=custom_slug).exists():
                return Response({'detail': f'URL "{custom_slug}" sudah dipakai. Coba yang lain.'}, status=400)
            slug = custom_slug
        else:
            slug = generate_slug(name)

        # Buat workspace
        workspace = Workspace.objects.create(
            name=name,
            slug=slug,
            owner=request.user,
        )

        # Tambah owner sebagai admin
        role, _ = UserRole.objects.get_or_create(name='admin')
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=request.user,
            role=role,
            status='active',
            invited_by=request.user,
        )

        return Response({
            'id': str(workspace.id),
            'name': workspace.name,
            'slug': workspace.slug,
            'url': f'https://black-message.vercel.app/workspace/{workspace.slug}',
            'detail': f'Workspace "{name}" berhasil dibuat!',
        }, status=201)

    def get(self, request):
        """Cek ketersediaan slug."""
        slug = request.query_params.get('slug', '').strip().lower()
        if not slug:
            return Response({'detail': 'Slug diperlukan.'}, status=400)
        available = not Workspace.objects.filter(slug=slug).exists()
        return Response({
            'slug': slug,
            'available': available,
            'message': 'URL tersedia!' if available else 'URL sudah dipakai.',
        })
