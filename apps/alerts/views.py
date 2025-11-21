"""
Views para o sistema de Alertas e Regras
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import connection
from django.db.models import Q, Count

from .models import Rule, Alert, NotificationPreference
from .serializers import (
    RuleSerializer,
    AlertSerializer,
    AcknowledgeAlertSerializer,
    ResolveAlertSerializer,
    NotificationPreferenceSerializer,
    AlertStatisticsSerializer,
)
from apps.accounts.permissions import IsTenantMember, CanWrite

logger = logging.getLogger(__name__)


class RuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar Regras de Alerta
    
    list: Listar todas as regras do tenant
    create: Criar nova regra
    retrieve: Obter detalhes de uma regra
    update: Atualizar regra
    partial_update: Atualizar parcialmente regra
    destroy: Deletar regra
    toggle_status: Ativar/desativar regra
    """
    
    serializer_class = RuleSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    
    def get_queryset(self):
        """Filtra regras do tenant atual"""
        queryset = Rule.objects.select_related(
            'equipment',
            'created_by'
        ).all()
        
        # Filtros opcionais
        enabled = self.request.query_params.get('enabled')
        if enabled is not None:
            queryset = queryset.filter(enabled=enabled.lower() == 'true')
        
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity__iexact=severity)  # 🔧 Case-insensitive (aceita CRITICAL ou Critical)
        
        equipment_id = self.request.query_params.get('equipment_id')
        if equipment_id:
            queryset = queryset.filter(equipment_id=equipment_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Salva o criador da regra"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsTenantMember, CanWrite])
    def toggle_status(self, request, pk=None):
        """Ativa/desativa uma regra"""
        rule = self.get_object()
        old_status = rule.enabled
        rule.enabled = not rule.enabled
        rule.save(update_fields=['enabled', 'updated_at'])
        
        logger.info(
            f"🔄 Rule #{rule.id} '{rule.name}' status changed: "
            f"{old_status} → {rule.enabled} by user {request.user.email}"
        )
        
        serializer = self.get_serializer(rule)
        return Response({
            'status': 'enabled' if rule.enabled else 'disabled',
            'rule': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Retorna estatísticas das regras"""
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'enabled': queryset.filter(enabled=True).count(),
            'disabled': queryset.filter(enabled=False).count(),
            'by_severity': {
                'Critical': queryset.filter(severity='Critical').count(),
                'High': queryset.filter(severity='High').count(),
                'Medium': queryset.filter(severity='Medium').count(),
                'Low': queryset.filter(severity='Low').count(),
            }
        }
        
        return Response(stats)


class AlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar Alertas
    
    list: Listar todos os alertas do tenant
    create: Criar novo alerta (geralmente feito automaticamente pelo sistema)
    retrieve: Obter detalhes de um alerta
    update: Atualizar alerta
    destroy: Deletar alerta
    acknowledge: Reconhecer alerta
    resolve: Resolver alerta
    statistics: Estatísticas de alertas
    """
    
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    
    def get_queryset(self):
        """Filtra alertas do tenant atual"""
        queryset = Alert.objects.select_related(
            'rule',
            'rule__equipment',
            'acknowledged_by',
            'resolved_by'
        ).all()
        
        # Filtros opcionais
        status_filter = self.request.query_params.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(acknowledged=False, resolved=False)
        elif status_filter == 'acknowledged':
            queryset = queryset.filter(acknowledged=True, resolved=False)
        elif status_filter == 'resolved':
            queryset = queryset.filter(resolved=True)
        
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity__iexact=severity)  # 🔧 Case-insensitive (aceita CRITICAL ou Critical)
        
        rule_id = self.request.query_params.get('rule_id')
        if rule_id:
            queryset = queryset.filter(rule_id=rule_id)
        
        asset_tag = self.request.query_params.get('asset_tag')
        if asset_tag:
            queryset = queryset.filter(asset_tag__icontains=asset_tag)
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsTenantMember, CanWrite])
    def acknowledge(self, request, pk=None):
        """Reconhece um alerta"""
        alert = self.get_object()
        
        if alert.acknowledged:
            return Response(
                {'error': 'Alerta já foi reconhecido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AcknowledgeAlertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        alert.acknowledged = True
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = request.user
        
        notes = serializer.validated_data.get('notes', '')
        if notes:
            alert.notes = f"{alert.notes}\n[Reconhecimento] {notes}" if alert.notes else f"[Reconhecimento] {notes}"
        
        alert.save()
        
        response_serializer = self.get_serializer(alert)
        return Response({
            'status': 'acknowledged',
            'alert': response_serializer.data
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsTenantMember, CanWrite])
    def resolve(self, request, pk=None):
        """Resolve um alerta"""
        alert = self.get_object()
        
        if alert.resolved:
            return Response(
                {'error': 'Alerta já foi resolvido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ResolveAlertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        alert.resolved = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        
        # Se não estava reconhecido, reconhece automaticamente
        if not alert.acknowledged:
            alert.acknowledged = True
            alert.acknowledged_at = timezone.now()
            alert.acknowledged_by = request.user
        
        notes = serializer.validated_data.get('notes', '')
        if notes:
            alert.notes = f"{alert.notes}\n[Resolução] {notes}" if alert.notes else f"[Resolução] {notes}"
        
        alert.save()
        
        response_serializer = self.get_serializer(alert)
        return Response({
            'status': 'resolved',
            'alert': response_serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Retorna estatísticas dos alertas"""
        queryset = self.get_queryset()
        
        # Padronizar severidades em MAIÚSCULAS para consistência com frontend
        stats = {
            'total': queryset.count(),
            'active': queryset.filter(acknowledged=False, resolved=False).count(),
            'acknowledged': queryset.filter(acknowledged=True, resolved=False).count(),
            'resolved': queryset.filter(resolved=True).count(),
            'by_severity': {
                'CRITICAL': queryset.filter(severity='Critical').count(),
                'HIGH': queryset.filter(severity='High').count(),
                'MEDIUM': queryset.filter(severity='Medium').count(),
                'LOW': queryset.filter(severity='Low').count(),
            }
        }
        
        serializer = AlertStatisticsSerializer(stats)
        return Response(serializer.data)


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar Preferências de Notificação
    
    list: Listar preferências (geralmente apenas a do usuário logado)
    retrieve: Obter preferências de um usuário
    update: Atualizar preferências
    partial_update: Atualizar parcialmente
    me: Obter/atualizar preferências do usuário logado
    """
    
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    
    def get_queryset(self):
        """Filtra preferências do tenant atual"""
        # Usuários normais só veem suas próprias preferências
        if not self.request.user.is_staff:
            return NotificationPreference.objects.filter(user=self.request.user)
        
        # Staff pode ver todas
        return NotificationPreference.objects.select_related('user').all()
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """Obter ou atualizar preferências do usuário logado"""
        # Buscar ou criar preferências
        preference, created = NotificationPreference.objects.get_or_create(
            user=request.user,
            defaults={
                'email_enabled': True,
                'push_enabled': True,
                'sound_enabled': True,
                'sms_enabled': False,
                'whatsapp_enabled': False,
                'critical_alerts': True,
                'high_alerts': True,
                'medium_alerts': True,
                'low_alerts': False,
            }
        )
        
        if request.method == 'GET':
            serializer = self.get_serializer(preference)
            return Response(serializer.data)
        
        # PUT ou PATCH
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(preference, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)

