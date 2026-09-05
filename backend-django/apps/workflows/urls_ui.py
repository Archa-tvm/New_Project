from django.urls import path
from .views_ui import (
    dashboard_view,
    workflow_detail_view,
    instance_detail_view,
    approve_task_view
)

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('workflow/<uuid:workflow_id>/', workflow_detail_view, name='workflow-detail'),
    path('instance/<uuid:instance_id>/', instance_detail_view, name='instance-detail'),
    path('approval/<uuid:task_id>/decide/', approve_task_view, name='approval-decide'),
]
