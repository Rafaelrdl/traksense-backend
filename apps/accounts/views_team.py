"""
Views for team management (memberships and invites).
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import connection
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from .models import TenantMembership, Invite
from .serializers_team import (
    TenantMembershipSerializer,
    UpdateMembershipSerializer,
    InviteSerializer,
    CreateInviteSerializer,
    AcceptInviteSerializer,
    TeamStatsSerializer
)
from .permissions import CanManageTeam


class TeamMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing team members (memberships).
    
    List, retrieve, update, and remove team members.
    Only owners and admins can manage team.
    """
    
    serializer_class = TenantMembershipSerializer
    permission_classes = [IsAuthenticated, CanManageTeam]
    
    def get_queryset(self):
        """Get memberships for current tenant."""
        tenant = connection.tenant
        return TenantMembership.objects.filter(
            tenant=tenant
        ).select_related('user', 'invited_by').order_by('-joined_at')
    
    def get_serializer_class(self):
        """Use different serializer for updates."""
        if self.action in ['update', 'partial_update']:
            return UpdateMembershipSerializer
        return TenantMembershipSerializer
    
    def destroy(self, request, *args, **kwargs):
        """Remove member from team."""
        membership = self.get_object()
        tenant = connection.tenant
        
        # Prevent removing the last owner
        if membership.role == 'owner':
            other_owners = TenantMembership.objects.filter(
                tenant=tenant,
                role='owner',
                status='active'
            ).exclude(pk=membership.pk).count()
            
            if other_owners == 0:
                return Response(
                    {"detail": "Cannot remove the last owner from the organization."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Soft delete: set status to inactive instead of deleting
        membership.status = 'inactive'
        membership.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get team statistics.
        
        Returns counts of members by role and status.
        """
        tenant = connection.tenant
        
        # Count members
        total_members = TenantMembership.objects.filter(tenant=tenant).count()
        active_members = TenantMembership.objects.filter(
            tenant=tenant,
            status='active'
        ).count()
        
        # Count pending invites
        pending_invites = Invite.objects.filter(
            tenant=tenant,
            status='pending'
        ).count()
        
        # Count members by role
        members_by_role = TenantMembership.objects.filter(
            tenant=tenant,
            status='active'
        ).values('role').annotate(count=Count('id'))
        
        role_counts = {item['role']: item['count'] for item in members_by_role}
        
        members_by_status = TenantMembership.objects.filter(
            tenant=tenant
        ).values('status').annotate(count=Count('id'))
        status_counts = {item['status']: item['count'] for item in members_by_status}
        
        data = {
            'total_members': total_members,
            'active_members': active_members,
            'pending_invites': pending_invites,
            'members_by_role': role_counts,
            'members_by_status': status_counts
        }
        
        serializer = TeamStatsSerializer(data)
        return Response(serializer.data)


class InviteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing invitations.
    
    Create, list, and cancel invitations.
    Accept invitations via token.
    """
    
    serializer_class = InviteSerializer
    permission_classes = [IsAuthenticated, CanManageTeam]
    
    def get_queryset(self):
        """Get invites for current tenant."""
        tenant = connection.tenant
        return Invite.objects.filter(
            tenant=tenant
        ).select_related('invited_by', 'accepted_by').order_by('-created_at')
    
    def get_serializer_class(self):
        """Use different serializer for creation."""
        if self.action == 'create':
            return CreateInviteSerializer
        elif self.action == 'accept':
            return AcceptInviteSerializer
        return InviteSerializer
    
    def create(self, request, *args, **kwargs):
        """Create and send invitation."""
        tenant = connection.tenant
        
        serializer = self.get_serializer(
            data=request.data,
            context={'tenant': tenant}
        )
        serializer.is_valid(raise_exception=True)
        
        # Create invite
        invite = Invite.objects.create(
            tenant=tenant,
            invited_by=request.user,
            **serializer.validated_data
        )
        
        # Send invitation email
        self._send_invite_email(invite)
        
        # Return created invite
        response_serializer = InviteSerializer(invite)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def destroy(self, request, *args, **kwargs):
        """Cancel an invitation."""
        invite = self.get_object()
        
        if invite.status != 'pending':
            return Response(
                {"detail": "Only pending invitations can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invite.cancel()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def accept(self, request):
        """
        Accept an invitation using token.
        
        Creates membership and marks invite as accepted.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        invite = serializer.context['invite']
        
        try:
            # Accept invite and create membership
            membership = invite.accept(request.user)
            
            # Return membership details
            membership_serializer = TenantMembershipSerializer(membership)
            return Response(
                {
                    "message": "Invitation accepted successfully.",
                    "membership": membership_serializer.data
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Resend invitation email."""
        invite = self.get_object()
        
        if invite.status != 'pending':
            return Response(
                {"detail": "Only pending invitations can be resent."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not invite.is_valid:
            return Response(
                {"detail": "This invitation has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Resend email
        self._send_invite_email(invite)
        
        serializer = InviteSerializer(invite)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def _send_invite_email(self, invite):
        """
        Send invitation email to recipient.
        
        In production, this should use a proper email service (SendGrid, etc.)
        In development, emails go to console or Mailpit.
        """
        # Build acceptance URL
        accept_url = f"{settings.FRONTEND_URL}/accept-invite?token={invite.token}"
        
        # Email context
        context = {
            'invite': invite,
            'accept_url': accept_url,
            'tenant_name': invite.tenant.name,
            'invited_by_name': invite.invited_by.full_name if invite.invited_by else 'Team',
            'role': invite.get_role_display(),
        }
        
        # Render email template
        subject = f"You've been invited to join {invite.tenant.name}"
        html_message = render_to_string('emails/team_invite.html', context)
        plain_message = render_to_string('emails/team_invite.txt', context)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invite.email],
            html_message=html_message,
            fail_silently=False,
        )
