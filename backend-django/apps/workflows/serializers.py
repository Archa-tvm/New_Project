from rest_framework import serializers
from .models import WorkflowDefinition, WorkflowInstance, StepExecution, ApprovalTask

class StepExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepExecution
        fields = [
            'id', 'node_id', 'node_name', 'node_type', 'status',
            'input_data', 'output_data', 'error_message', 'duration_ms',
            'started_at', 'completed_at'
        ]

class ApprovalTaskSerializer(serializers.ModelSerializer):
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    decision_by_username = serializers.CharField(source='decision_by.username', read_only=True)

    class Meta:
        model = ApprovalTask
        fields = [
            'id', 'instance', 'step_execution', 'assigned_role', 'assigned_to',
            'assigned_to_username', 'title', 'description', 'status',
            'decision_by', 'decision_by_username', 'decision_note',
            'decided_at', 'created_at'
        ]

class WorkflowInstanceSerializer(serializers.ModelSerializer):
    definition_name = serializers.CharField(source='definition.name', read_only=True)
    step_executions = StepExecutionSerializer(many=True, read_only=True)
    approval_tasks = ApprovalTaskSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowInstance
        fields = [
            'id', 'tenant', 'definition', 'definition_name', 'triggered_by',
            'status', 'current_step', 'input_payload', 'output_payload',
            'error_message', 'started_at', 'completed_at',
            'step_executions', 'approval_tasks'
        ]

class WorkflowDefinitionSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    instances_count = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowDefinition
        fields = [
            'id', 'tenant', 'tenant_name', 'name', 'slug', 'description',
            'trigger_type', 'graph_schema', 'version', 'is_active',
            'instances_count', 'created_at', 'updated_at'
        ]

    def get_instances_count(self, obj):
        return obj.instances.count()

class TriggerWorkflowSerializer(serializers.Serializer):
    payload = serializers.JSONField(default=dict, required=False)

class ApprovalDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['approved', 'rejected'])
    note = serializers.CharField(required=False, allow_blank=True, default='')
