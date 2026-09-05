import pytest
from rest_framework.test import APIClient
from apps.tenants.models import Tenant
from apps.workflows.models import WorkflowDefinition

@pytest.mark.django_db
def test_workflow_api_crud():
    client = APIClient()
    tenant = Tenant.objects.create(name='Globex', slug='globex')
    
    # Create Definition
    payload = {
        'tenant': str(tenant.id),
        'name': 'API Workflow',
        'slug': 'api-workflow',
        'trigger_type': 'manual',
        'graph_schema': {'nodes': []}
    }
    res = client.post('/api/v1/workflows/definitions/', payload, format='json')
    assert res.status_code == 201
    wf_id = res.data['id']

    # Trigger execution endpoint
    trigger_res = client.post(f'/api/v1/workflows/definitions/{wf_id}/trigger/', {'payload': {'test': True}}, format='json')
    assert trigger_res.status_code == 201
    assert 'instance_id' in trigger_res.data
