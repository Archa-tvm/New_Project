from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import WorkflowDefinition, WorkflowInstance, StepExecution, ApprovalTask
from .serializers import (
    WorkflowDefinitionSerializer,
    WorkflowInstanceSerializer,
    StepExecutionSerializer,
    ApprovalTaskSerializer,
    TriggerWorkflowSerializer,
    ApprovalDecisionSerializer
)
from .engine_client import engine_client

class WorkflowDefinitionViewSet(viewsets.ModelViewSet):
    queryset = WorkflowDefinition.objects.select_related('tenant').all()
    serializer_class = WorkflowDefinitionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_slug = self.request.query_params.get('tenant')
        if tenant_slug:
            qs = qs.filter(tenant__slug=tenant_slug)
        return qs

    @action(detail=True, methods=['post'], url_path='trigger')
    def trigger(self, request, pk=None):
        """Trigger an execution of this workflow definition."""
        workflow = self.get_object()
        serializer = TriggerWorkflowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data.get('payload', {})

        instance = WorkflowInstance.objects.create(
            tenant=workflow.tenant,
            definition=workflow,
            triggered_by=request.user if request.user.is_authenticated else None,
            status='pending',
            input_payload=payload
        )

        # Notify C# .NET Workflow Engine
        dispatched, engine_msg = engine_client.trigger_execution(instance.id, payload)

        return Response({
            'instance_id': str(instance.id),
            'status': instance.status,
            'engine_dispatched': dispatched,
            'engine_response': engine_msg
        }, status=status.HTTP_201_CREATED)

class WorkflowInstanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowInstance.objects.select_related('definition', 'tenant').prefetch_related('step_executions', 'approval_tasks').all()
    serializer_class = WorkflowInstanceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = self.request.query_params.get('tenant_id')
        definition_id = self.request.query_params.get('definition_id')
        status_filter = self.request.query_params.get('status')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if definition_id:
            qs = qs.filter(definition_id=definition_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        instance = self.get_object()
        if instance.status in ('completed', 'failed', 'cancelled'):
            return Response({'error': f'Cannot cancel instance with status {instance.status}'}, status=status.HTTP_400_BAD_REQUEST)

        instance.status = 'cancelled'
        instance.completed_at = timezone.now()
        instance.error_message = 'Manually cancelled by user.'
        instance.save(update_fields=['status', 'completed_at', 'error_message'])
        return Response({'message': 'Workflow instance cancelled successfully.'})

class ApprovalTaskViewSet(viewsets.ModelViewSet):
    queryset = ApprovalTask.objects.select_related('instance', 'assigned_to', 'decision_by').all()
    serializer_class = ApprovalTaskSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=['post'], url_path='decide')
    def decide(self, request, pk=None):
        task = self.get_object()
        if task.status != 'pending':
            return Response({'error': 'Task is already decided.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ApprovalDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = serializer.validated_data['decision']
        note = serializer.validated_data.get('note', '')

        task.status = decision
        task.decision_by = request.user if request.user.is_authenticated else None
        task.decision_note = note
        task.decided_at = timezone.now()
        task.save()

        # Inform C# Engine to resume state machine execution
        engine_client.resume_approval(str(task.id), decision, note)

        return Response({
            'message': f'Approval task has been {decision}.',
            'task': ApprovalTaskSerializer(task).data
        })

class EngineHealthAPIView(APIView):
    def get(self, request):
        is_healthy, response_data = engine_client.check_health()
        return Response({
            'engine_online': is_healthy,
            'details': response_data
        })
