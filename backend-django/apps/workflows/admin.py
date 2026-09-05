from django.contrib import admin
from .models import WorkflowDefinition, WorkflowInstance, StepExecution, ApprovalTask

class StepExecutionInline(admin.TabularInline):
    model = StepExecution
    extra = 0
    readonly_fields = ('node_id', 'node_name', 'node_type', 'status', 'duration_ms', 'started_at', 'completed_at')

@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant', 'trigger_type', 'version', 'is_active', 'updated_at')
    list_filter = ('trigger_type', 'is_active', 'tenant')
    search_fields = ('name', 'slug', 'description')

@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'definition', 'tenant', 'status', 'current_step', 'started_at', 'completed_at')
    list_filter = ('status', 'definition__tenant', 'started_at')
    search_fields = ('id', 'definition__name')
    inlines = [StepExecutionInline]

@admin.register(StepExecution)
class StepExecutionAdmin(admin.ModelAdmin):
    list_display = ('instance', 'node_id', 'node_name', 'node_type', 'status', 'duration_ms', 'started_at')
    list_filter = ('node_type', 'status', 'started_at')
    search_fields = ('node_id', 'node_name', 'instance__id')

@admin.register(ApprovalTask)
class ApprovalTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'instance', 'assigned_role', 'assigned_to', 'status', 'decided_at')
    list_filter = ('status', 'assigned_role')
    search_fields = ('title', 'description', 'instance__id')
