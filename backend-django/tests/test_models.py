import pytest
from django.contrib.auth.models import User
from apps.tenants.models import Tenant, TenantMembership
from apps.workflows.models import WorkflowDefinition, WorkflowInstance, StepExecution, ApprovalTask

@pytest.mark.django_db
def test_tenant_creation():
    tenant = Tenant.objects.create(name='Test Corp', slug='test-corp', plan='growth')
    assert tenant.id is not None
    assert tenant.name == 'Test Corp'
    assert tenant.plan == 'growth'
    assert str(tenant) == 'Test Corp'

@pytest.mark.django_db
def test_workflow_definition_and_instance():
    tenant = Tenant.objects.create(name='Acme', slug='acme')
    user = User.objects.create_user(username='tester', password='pw')

    wf = WorkflowDefinition.objects.create(
        tenant=tenant,
        name='Invoice Review',
        slug='invoice-review',
        graph_schema={'nodes': [{'id': 'start', 'type': 'trigger'}]}
    )
    assert wf.version == 1

    instance = WorkflowInstance.objects.create(
        tenant=tenant,
        definition=wf,
        triggered_by=user,
        input_payload={'amount': 100}
    )
    assert instance.status == 'pending'

    step = StepExecution.objects.create(
        instance=instance,
        node_id='start',
        node_name='Start Node',
        node_type='trigger',
        status='completed',
        duration_ms=12
    )
    assert step.duration_ms == 12
    assert instance.step_executions.count() == 1
