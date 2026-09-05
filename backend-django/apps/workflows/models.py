import uuid
from django.db import models
from django.contrib.auth.models import User
from apps.tenants.models import Tenant

class WorkflowDefinition(models.Model):
    TRIGGER_CHOICES = [
        ('manual', 'Manual Trigger'),
        ('webhook', 'Incoming Webhook'),
        ('schedule', 'Cron Schedule'),
        ('event', 'Business Event'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='workflows')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True, default='')
    trigger_type = models.CharField(max_length=30, choices=TRIGGER_CHOICES, default='manual')
    graph_schema = models.JSONField(
        default=dict,
        help_text='JSON graph containing nodes, edges, transitions, and rules'
    )
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workflow_definitions'
        unique_together = ('tenant', 'slug')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} (v{self.version}) - {self.tenant.name}"

class WorkflowInstance(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('waiting_approval', 'Waiting for Approval'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='instances')
    definition = models.ForeignKey(WorkflowDefinition, on_delete=models.CASCADE, related_name='instances')
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    current_step = models.CharField(max_length=100, blank=True, default='')
    input_payload = models.JSONField(default=dict, blank=True)
    output_payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default='')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'workflow_instances'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.definition.name} #{str(self.id)[:8]} [{self.status}]"

class StepExecution(models.Model):
    NODE_TYPES = [
        ('trigger', 'Trigger Step'),
        ('condition', 'Conditional Branch'),
        ('http_webhook', 'HTTP Webhook Call'),
        ('approval', 'Approval Gate'),
        ('notification', 'Notification Dispatch'),
        ('transform', 'Data Transformation'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='step_executions')
    node_id = models.CharField(max_length=100)
    node_name = models.CharField(max_length=150, blank=True, default='')
    node_type = models.CharField(max_length=40, choices=NODE_TYPES, default='condition')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    input_data = models.JSONField(default=dict, blank=True)
    output_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default='')
    duration_ms = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'step_executions'
        ordering = ['started_at']

    def __str__(self):
        return f"{self.node_name or self.node_id} ({self.node_type}) - {self.status}"

class ApprovalTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='approval_tasks')
    step_execution = models.OneToOneField(
        StepExecution, on_delete=models.SET_NULL, null=True, blank=True, related_name='approval_task'
    )
    assigned_role = models.CharField(max_length=50, default='manager')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_approvals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    decision_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='decided_approvals')
    decision_note = models.TextField(blank=True, default='')
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'approval_tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f"Approval: {self.title} [{self.status}]"
