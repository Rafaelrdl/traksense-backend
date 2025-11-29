"""
Views para CMMS - Gestão de Manutenção
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    ChecklistTemplate, WorkOrder, WorkOrderPhoto, 
    WorkOrderItem, Request, RequestItem, MaintenancePlan
)
from .serializers import (
    ChecklistTemplateSerializer,
    WorkOrderSerializer, WorkOrderListSerializer, WorkOrderPhotoSerializer,
    WorkOrderItemSerializer, WorkOrderStatsSerializer,
    RequestSerializer, RequestListSerializer, RequestItemSerializer,
    ConvertToWorkOrderSerializer,
    MaintenancePlanSerializer, MaintenancePlanListSerializer
)


class ChecklistTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet para templates de checklist."""
    
    queryset = ChecklistTemplate.objects.all()
    serializer_class = ChecklistTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrar apenas ativos por padrão
        if self.action == 'list':
            is_active = self.request.query_params.get('is_active', 'true')
            if is_active.lower() == 'true':
                queryset = queryset.filter(is_active=True)
        return queryset


class WorkOrderViewSet(viewsets.ModelViewSet):
    """ViewSet para Ordens de Serviço."""
    
    queryset = WorkOrder.objects.select_related(
        'asset', 'asset__site', 'assigned_to', 'created_by',
        'checklist_template', 'request', 'maintenance_plan'
    ).prefetch_related('photos', 'items__inventory_item')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact', 'in'],
        'type': ['exact', 'in'],
        'priority': ['exact', 'in'],
        'asset': ['exact'],
        'assigned_to': ['exact'],
        'scheduled_date': ['exact', 'gte', 'lte'],
    }
    search_fields = ['number', 'description', 'asset__tag', 'asset__name']
    ordering_fields = ['number', 'scheduled_date', 'priority', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return WorkOrderListSerializer
        return WorkOrderSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Inicia a execução de uma OS."""
        work_order = self.get_object()
        
        if work_order.status != WorkOrder.Status.OPEN:
            return Response(
                {'error': 'Apenas OS abertas podem ser iniciadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        work_order.start()
        serializer = self.get_serializer(work_order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Conclui uma OS."""
        work_order = self.get_object()
        
        if work_order.status not in [WorkOrder.Status.OPEN, WorkOrder.Status.IN_PROGRESS]:
            return Response(
                {'error': 'Apenas OS abertas ou em andamento podem ser concluídas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        execution_description = request.data.get('execution_description', '')
        actual_hours = request.data.get('actual_hours')
        
        if actual_hours:
            actual_hours = float(actual_hours)
        
        work_order.complete(execution_description, actual_hours)
        
        # Atualizar respostas do checklist se fornecidas
        checklist_responses = request.data.get('checklist_responses')
        if checklist_responses:
            work_order.checklist_responses = checklist_responses
            work_order.save(update_fields=['checklist_responses'])
        
        serializer = self.get_serializer(work_order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancela uma OS."""
        work_order = self.get_object()
        
        if work_order.status in [WorkOrder.Status.COMPLETED, WorkOrder.Status.CANCELLED]:
            return Response(
                {'error': 'OS já concluída ou cancelada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        if not reason:
            return Response(
                {'error': 'Motivo do cancelamento é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        work_order.cancel(reason)
        serializer = self.get_serializer(work_order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def photos(self, request, pk=None):
        """Upload de foto para a OS."""
        work_order = self.get_object()
        
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'Arquivo não fornecido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        photo = WorkOrderPhoto.objects.create(
            work_order=work_order,
            file=file,
            caption=request.data.get('caption', ''),
            uploaded_by=request.user
        )
        
        serializer = WorkOrderPhotoSerializer(photo)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='items')
    def add_item(self, request, pk=None):
        """Adiciona item de estoque à OS."""
        work_order = self.get_object()
        
        serializer = WorkOrderItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(work_order=work_order)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retorna estatísticas das OS."""
        queryset = self.get_queryset()
        today = timezone.now().date()
        
        # Contagens por status
        status_counts = queryset.values('status').annotate(count=Count('id'))
        status_dict = {item['status']: item['count'] for item in status_counts}
        
        # Contagens por tipo
        type_counts = queryset.values('type').annotate(count=Count('id'))
        type_dict = {item['type'].lower(): item['count'] for item in type_counts}
        
        # Contagens por prioridade
        priority_counts = queryset.values('priority').annotate(count=Count('id'))
        priority_dict = {item['priority'].lower(): item['count'] for item in priority_counts}
        
        # Atrasadas
        overdue_count = queryset.filter(
            status__in=[WorkOrder.Status.OPEN, WorkOrder.Status.IN_PROGRESS],
            scheduled_date__lt=today
        ).count()
        
        stats = {
            'total': queryset.count(),
            'open': status_dict.get('OPEN', 0),
            'in_progress': status_dict.get('IN_PROGRESS', 0),
            'completed': status_dict.get('COMPLETED', 0),
            'overdue': overdue_count,
            'by_type': type_dict,
            'by_priority': priority_dict,
        }
        
        serializer = WorkOrderStatsSerializer(stats)
        return Response(serializer.data)


class RequestViewSet(viewsets.ModelViewSet):
    """ViewSet para Solicitações."""
    
    queryset = Request.objects.select_related(
        'sector', 'subsection', 'asset', 'requester'
    ).prefetch_related('items__inventory_item')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact', 'in'],
        'sector': ['exact'],
        'subsection': ['exact'],
        'asset': ['exact'],
        'requester': ['exact'],
    }
    search_fields = ['number', 'note', 'asset__tag']
    ordering_fields = ['number', 'status', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return RequestListSerializer
        return RequestSerializer

    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)

    @action(detail=True, methods=['post'])
    def convert(self, request, pk=None):
        """Converte solicitação em ordem de serviço."""
        req = self.get_object()
        
        if req.status == Request.Status.CONVERTED:
            return Response(
                {'error': 'Solicitação já foi convertida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if req.status == Request.Status.REJECTED:
            return Response(
                {'error': 'Solicitação rejeitada não pode ser convertida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ConvertToWorkOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Criar OS
        wo_data = serializer.validated_data
        work_order = WorkOrder.objects.create(
            asset=req.asset,
            type=wo_data['type'],
            priority=wo_data['priority'],
            scheduled_date=wo_data['scheduled_date'],
            assigned_to=wo_data.get('assigned_to'),
            description=wo_data.get('description') or req.note,
            request=req,
            created_by=request.user
        )
        
        # Atualizar status da solicitação
        req.update_status(Request.Status.CONVERTED, request.user)
        
        return Response({
            'request': RequestSerializer(req).data,
            'work_order_id': work_order.id,
            'work_order_number': work_order.number,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='items')
    def add_item(self, request, pk=None):
        """Adiciona item à solicitação."""
        req = self.get_object()
        
        serializer = RequestItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request=req)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def counts(self, request):
        """Retorna contagens por status."""
        queryset = self.get_queryset()
        
        counts = queryset.values('status').annotate(count=Count('id'))
        result = {item['status'].lower(): item['count'] for item in counts}
        
        # Garantir que todas as chaves existem
        for status_choice in Request.Status.choices:
            key = status_choice[0].lower()
            if key not in result:
                result[key] = 0
        
        return Response(result)


class MaintenancePlanViewSet(viewsets.ModelViewSet):
    """ViewSet para Planos de Manutenção."""
    
    queryset = MaintenancePlan.objects.prefetch_related(
        'assets', 'checklist_template'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'is_active': ['exact'],
        'frequency': ['exact', 'in'],
    }
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'next_execution', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return MaintenancePlanListSerializer
        return MaintenancePlanSerializer

    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Gera ordens de serviço para o plano."""
        plan = self.get_object()
        
        if not plan.is_active:
            return Response(
                {'error': 'Plano inativo não pode gerar OS'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not plan.assets.exists():
            return Response(
                {'error': 'Plano não possui ativos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        work_order_ids = plan.generate_work_orders(request.user)
        
        return Response({
            'work_orders_created': len(work_order_ids),
            'work_order_ids': work_order_ids,
            'next_execution': plan.next_execution.isoformat() if plan.next_execution else None,
        })

    @action(detail=True, methods=['post'], url_path='assets')
    def add_asset(self, request, pk=None):
        """Adiciona ativo ao plano."""
        plan = self.get_object()
        asset_id = request.data.get('asset')
        
        if not asset_id:
            return Response(
                {'error': 'ID do ativo é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        plan.assets.add(asset_id)
        return Response({'status': 'ok'})

    @action(detail=True, methods=['delete'], url_path='assets/(?P<asset_id>[^/.]+)')
    def remove_asset(self, request, pk=None, asset_id=None):
        """Remove ativo do plano."""
        plan = self.get_object()
        plan.assets.remove(asset_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retorna estatísticas dos planos."""
        queryset = self.get_queryset()
        
        # Contagens
        total = queryset.count()
        active = queryset.filter(is_active=True).count()
        inactive = total - active
        
        # Por frequência
        freq_counts = queryset.values('frequency').annotate(count=Count('id'))
        by_frequency = {item['frequency'].lower(): item['count'] for item in freq_counts}
        
        # Próximas execuções (top 5)
        next_executions = queryset.filter(
            is_active=True,
            next_execution__isnull=False
        ).order_by('next_execution')[:5].values('id', 'name', 'next_execution')
        
        return Response({
            'total': total,
            'active': active,
            'inactive': inactive,
            'by_frequency': by_frequency,
            'next_executions': [
                {
                    'plan_id': item['id'],
                    'plan_name': item['name'],
                    'next_date': item['next_execution'].isoformat() if item['next_execution'] else None
                }
                for item in next_executions
            ]
        })
