from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkflowDefinitionViewSet,
    WorkflowInstanceViewSet,
    ApprovalTaskViewSet,
    EngineHealthAPIView
)

router = DefaultRouter()
router.register(r'definitions', WorkflowDefinitionViewSet, basename='workflow-definition')
router.register(r'instances', WorkflowInstanceViewSet, basename='workflow-instance')
router.register(r'approvals', ApprovalTaskViewSet, basename='approval-task')

urlpatterns = [
    path('', include(router.urls)),
    path('engine/health/', EngineHealthAPIView.as_view(), name='engine-health'),
]
