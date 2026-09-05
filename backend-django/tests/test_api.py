from rest_framework.test import APITestCase
from rest_framework import status
from apps.tenants.models import Tenant
from apps.workflows.models import WorkflowDefinition

class WorkflowAPITestCase(APITestCase):
    def test_workflow_api_crud_and_trigger(self):
        tenant = Tenant.objects.create(name='Globex', slug='globex')

        # Create Definition
        payload = {
            'tenant': str(tenant.id),
            'name': 'API Workflow',
            'slug': 'api-workflow',
            'trigger_type': 'manual',
            'graph_schema': {'nodes': []}
        }
        res = self.client.post('/api/v1/workflows/definitions/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        wf_id = res.data['id']

        # Trigger execution endpoint
        trigger_res = self.client.post(
            f'/api/v1/workflows/definitions/{wf_id}/trigger/',
            {'payload': {'test': True}},
            format='json'
        )
        self.assertEqual(trigger_res.status_code, status.HTTP_201_CREATED)
        self.assertIn('instance_id', trigger_res.data)
