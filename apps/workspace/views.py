"""
apps/workspace/views.py
Workspace & Channel management — 15 endpoints.

  POST   /workspaces/                         — Create workspace
  GET    /workspaces/                         — List my workspaces
  GET    /workspaces/{slug}/                  — Workspace detail
  PATCH  /workspaces/{slug}/                  — Update workspace
  DELETE /workspaces/{slug}/                  — Archive workspace
  GET    /workspaces/{slug}/channels/         — List channels
  POST   /workspaces/{slug}/channels/         — Create channel
  GET    /workspaces/{slug}/channels/{id}/    — Channel detail
  PATCH  /workspaces/{slug}/channels/{id}/    — Update channel
  DELETE /workspaces/{slug}/channels/{id}/    — Archive channel
  POST   /workspaces/{slug}/channels/{id}/join/    — Join channel
  POST   /workspaces/{slug}/channels/{id}/leave/   — Leave channel
  GET    /workspaces/{slug}/members/          — List members
  GET    /workspaces/{slug}/presence/         — Live presence
  PATCH  /workspaces/{slug}/settings/         — Update settings
"""

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Workspace, WorkspaceMember, Channel, ChannelMember, UserPresence, WorkspaceSettings
from .serializers import (WorkspaceSerializer, ChannelSerializer,
                          ChannelMemberSerializer, UserPresenceSerializer, WorkspaceSettingsSerializer)
from .permissions import IsWorkspaceMember, IsWorkspaceAdmin
from apps.users.permissions import IsMFAVerified


class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated, IsMFAVerified]
    lookup_field = "slug"

    def get_queryset(self):
        return Workspace.objects.filter(
            members__user=self.request.user,
            members__status="active",
            is_active=True,
        ).distinct()

    def perform_create(self, serializer):
        workspace = serializer.save(owner=self.request.user)
        # Auto-add creator as admin member
        from apps.users.models import UserRole
        admin_role, _ = UserRole.objects.get_or_create(name="branch_manager", defaults={"display_name": "Branch Manager"})
        WorkspaceMember.objects.create(
            workspace=workspace, user=self.request.user, role=admin_role, status="active"
        )
        WorkspaceSettings.objects.create(workspace=workspace)

    @action(detail=True, methods=["get"])
    def members(self, request, slug=None):
        workspace = self.get_object()
        members = workspace.members.filter(status="active").select_related("user", "role")
        serializer = ChannelMemberSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def presence(self, request, slug=None):
        workspace = self.get_object()
        presences = UserPresence.objects.filter(
            workspace=workspace,
            user__workspace_memberships__workspace=workspace,
            user__workspace_memberships__status="active",
        ).select_related("user")
        return Response(UserPresenceSerializer(presences, many=True).data)

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated, IsWorkspaceAdmin])
    def workspace_settings(self, request, slug=None):
        workspace = self.get_object()
        instance, _ = WorkspaceSettings.objects.get_or_create(workspace=workspace)
        serializer = WorkspaceSettingsSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChannelViewSet(viewsets.ModelViewSet):
    serializer_class = ChannelSerializer
    permission_classes = [IsAuthenticated, IsMFAVerified, IsWorkspaceMember]

    def get_workspace(self):
        return get_object_or_404(Workspace, slug=self.kwargs["workspace_slug"], is_active=True)

    def get_queryset(self):
        workspace = self.get_workspace()
        user = self.request.user
        return Channel.objects.filter(
            workspace=workspace,
            memberships__user=user,
            is_archived=False,
        ).distinct().order_by("name")

    def perform_create(self, serializer):
        workspace = self.get_workspace()
        channel = serializer.save(workspace=workspace, created_by=self.request.user)
        ChannelMember.objects.create(channel=channel, user=self.request.user, is_admin=True)

    @action(detail=True, methods=["post"])
    def join(self, request, workspace_slug=None, pk=None):
        channel = self.get_object()
        if channel.channel_type == "private":
            return Response({"detail": "Private channels require an invite."}, status=403)
        ChannelMember.objects.get_or_create(channel=channel, user=request.user)
        return Response({"detail": "Joined channel."})

    @action(detail=True, methods=["post"])
    def leave(self, request, workspace_slug=None, pk=None):
        channel = self.get_object()
        ChannelMember.objects.filter(channel=channel, user=request.user).delete()
        return Response({"detail": "Left channel."})
