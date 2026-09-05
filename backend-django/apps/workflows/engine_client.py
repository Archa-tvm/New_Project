import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class DotNetWorkflowEngineClient:
    """HTTP Client to interact with the C# .NET Workflow Execution Engine."""

    def __init__(self, base_url=None):
        self.base_url = base_url or getattr(settings, 'WORKFLOW_ENGINE_URL', 'http://engine-dotnet:5050')

    def check_health(self):
        """Query health endpoint of C# engine."""
        url = f"{self.base_url}/api/v1/engine/health"
        try:
            resp = requests.get(url, timeout=3)
            return resp.status_code == 200, resp.json() if resp.status_code == 200 else resp.text
        except Exception as ex:
            logger.warning("DotNet engine unreachable: %s", str(ex))
            return False, str(ex)

    def trigger_execution(self, instance_id: str, input_payload: dict):
        """Dispatch execution order to C# .NET Workflow State Machine."""
        url = f"{self.base_url}/api/v1/engine/execute"
        payload = {
            "instanceId": str(instance_id),
            "payload": input_payload or {}
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code in (200, 202):
                return True, resp.json()
            return False, f"Engine returned status {resp.status_code}: {resp.text}"
        except Exception as ex:
            logger.error("Failed to connect to C# .NET engine at %s: %s", url, str(ex))
            return False, f"Connection error: {str(ex)}"

    def resume_approval(self, approval_task_id: str, decision: str, decision_note: str = ""):
        """Inform C# engine of human approval resolution."""
        url = f"{self.base_url}/api/v1/engine/resume"
        payload = {
            "taskId": str(approval_task_id),
            "decision": decision,
            "decisionNote": decision_note
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            return resp.status_code in (200, 202), resp.text
        except Exception as ex:
            logger.error("Failed to resume workflow on C# engine: %s", str(ex))
            return False, str(ex)

engine_client = DotNetWorkflowEngineClient()
