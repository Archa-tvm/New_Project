from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from apps.tenants.models import Tenant
from .models import WorkflowDefinition, WorkflowInstance, StepExecution, ApprovalTask
from .engine_client import engine_client

def dashboard_view(request):
    """Main SaaS operational dashboard."""
    tenant = Tenant.objects.first()
    workflows = WorkflowDefinition.objects.filter(tenant=tenant) if tenant else WorkflowDefinition.objects.all()
    instances = WorkflowInstance.objects.select_related('definition').order_by('-started_at')[:10]
    pending_approvals = ApprovalTask.objects.filter(status='pending').select_related('instance')

    total_workflows = workflows.count()
    total_instances = WorkflowInstance.objects.count()
    running_instances = WorkflowInstance.objects.filter(status='running').count()
    completed_instances = WorkflowInstance.objects.filter(status='completed').count()

    is_engine_healthy, engine_details = engine_client.check_health()

    context = {
        'tenant': tenant,
        'workflows': workflows,
        'recent_instances': instances,
        'pending_approvals': pending_approvals,
        'stats': {
            'total_workflows': total_workflows,
            'total_instances': total_instances,
            'running_instances': running_instances,
            'completed_instances': completed_instances,
        },
        'engine_healthy': is_engine_healthy,
        'engine_details': engine_details
    }
    return render(request, 'dashboard.html', context)

def workflow_detail_view(request, workflow_id):
    """Workflow detail and execution trigger view."""
    workflow = get_object_or_404(WorkflowDefinition, id=workflow_id)
    instances = workflow.instances.all().order_by('-started_at')[:15]

    if request.method == 'POST' and 'trigger_workflow' in request.POST:
        # User pressed 'Run Workflow' button
        instance = WorkflowInstance.objects.create(
            tenant=workflow.tenant,
            definition=workflow,
            status='pending',
            input_payload={
                'source': 'web_ui_manual_trigger',
                'amount': float(request.POST.get('amount', 5000)),
                'department': request.POST.get('department', 'Engineering'),
                'vendor': request.POST.get('vendor', 'Cloud Infra Corp')
            }
        )
        engine_client.trigger_execution(str(instance.id), instance.input_payload)
        messages.success(request, f"Workflow triggered! Instance ID: {str(instance.id)[:8]}")
        return redirect('workflow-detail', workflow_id=workflow.id)

    context = {
        'workflow': workflow,
        'instances': instances,
    }
    return render(request, 'workflow_detail.html', context)

def instance_detail_view(request, instance_id):
    """Detailed view of a single workflow execution with all step logs."""
    instance = get_object_or_404(
        WorkflowInstance.objects.select_related('definition', 'tenant').prefetch_related('step_executions', 'approval_tasks'),
        id=instance_id
    )
    context = {
        'instance': instance,
        'steps': instance.step_executions.all(),
        'approvals': instance.approval_tasks.all()
    }
    return render(request, 'instance_detail.html', context)

def approve_task_view(request, task_id):
    """Handle instant UI approval or rejection."""
    task = get_object_or_404(ApprovalTask, id=task_id)
    decision = request.POST.get('decision', 'approved')
    note = request.POST.get('note', 'Approved via FlowPulse Web UI')

    task.status = decision
    task.decision_note = note
    task.save()

    engine_client.resume_approval(str(task.id), decision, note)
    messages.success(request, f"Task {decision.upper()} successfully.")
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
