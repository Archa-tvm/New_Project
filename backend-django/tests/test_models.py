from django.test import TestCase
from django.contrib.auth.models import User
from apps.tenants.models import Tenant, TenantMembership
from apps.workflows.models import WorkflowDefinition, WorkflowInstance, StepExecution, ApprovalTask

class ModelTestCase(TestCase):
    def test_tenant_creation(self):
        tenant = Tenant.objects.create(name='Test Corp', slug='test-corp', plan='growth')
        self.assertIsNotNone(tenant.id)
        self.assertEqual(tenant.name, 'Test Corp')
        self.assertEqual(tenant.plan, 'growth')
        self.assertEqual(str(tenant), 'Test Corp')

    def test_workflow_definition_and_instance(self):
        tenant = Tenant.objects.create(name='Acme', slug='acme')
        user = User.objects.create_user(username='tester', password='pw')

        wf = WorkflowDefinition.objects.create(
            tenant=tenant,
            name='Invoice Review',
            slug='invoice-review',
            graph_schema={'nodes': [{'id': 'start', 'type': 'trigger'}]}
        )
        self.assertEqual(wf.version, 1)

        instance = WorkflowInstance.objects.create(
            tenant=tenant,
            definition=wf,
            triggered_by=user,
            input_payload={'amount': 100}
        )
        self.assertEqual(instance.status, 'pending')

        step = StepExecution.objects.create(
            instance=instance,
            node_id='start',
            node_name='Start Node',
            node_type='trigger',
            status='completed',
            duration_ms=12
        )
        self.assertEqual(step.duration_ms, 12)
        self.assertEqual(instance.step_executions.count(), 1)
