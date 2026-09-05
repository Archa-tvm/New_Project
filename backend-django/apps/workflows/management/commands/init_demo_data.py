from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from apps.tenants.models import Tenant, TenantMembership
from apps.workflows.models import WorkflowDefinition, WorkflowInstance, StepExecution, ApprovalTask

class Command(BaseCommand):
    help = 'Seeds initial multi-tenant organization, sample workflows, and demo executions.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding initial SaaS data...')

        # 1. Superuser
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@flowpulse.io',
                'first_name': 'Chief',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created default admin user: admin / admin123'))

        # 2. Default SaaS Tenant
        tenant, created = Tenant.objects.get_or_create(
            slug='apex-corp',
            defaults={
                'name': 'Apex Global Enterprise',
                'contact_email': 'ops@apexcorp.com',
                'plan': 'enterprise',
                'settings': {'region': 'us-east-1', 'currency': 'USD'}
            }
        )

        TenantMembership.objects.get_or_create(
            tenant=tenant,
            user=admin_user,
            defaults={'role': 'owner'}
        )

        # 3. Workflow 1: Procurement & Expense Approval
        wf_procure, _ = WorkflowDefinition.objects.get_or_create(
            tenant=tenant,
            slug='procurement-approval',
            defaults={
                'name': 'Procurement & Expense Approval',
                'description': 'Multi-step invoice and purchase order approval pipeline with policy rules and automated ERP integration.',
                'trigger_type': 'manual',
                'version': 1,
                'graph_schema': {
                    'nodes': [
                        {
                            'id': 'trigger_node',
                            'type': 'trigger',
                            'label': 'Purchase Order Submitted',
                            'config': {'source': 'web_form_or_api'}
                        },
                        {
                            'id': 'policy_check',
                            'type': 'condition',
                            'label': 'Budget & Compliance Validation',
                            'config': {
                                'field': 'amount',
                                'operator': 'greater_than',
                                'threshold': 5000,
                                'on_true': 'approval_gate',
                                'on_false': 'erp_sync'
                            }
                        },
                        {
                            'id': 'approval_gate',
                            'type': 'approval',
                            'label': 'Executive Finance Approval',
                            'config': {'required_role': 'manager', 'timeout_hours': 48}
                        },
                        {
                            'id': 'erp_sync',
                            'type': 'http_webhook',
                            'label': 'ERP Ledger Synchronization',
                            'config': {
                                'url': 'https://httpbin.org/post',
                                'method': 'POST',
                                'retry_count': 3
                            }
                        },
                        {
                            'id': 'notify_requester',
                            'type': 'notification',
                            'label': 'Notification & Audit Event',
                            'config': {'channel': 'slack_and_email', 'template': 'po_approved'}
                        }
                    ],
                    'edges': [
                        {'source': 'trigger_node', 'target': 'policy_check'},
                        {'source': 'policy_check', 'target': 'approval_gate', 'condition': 'requires_approval'},
                        {'source': 'approval_gate', 'target': 'erp_sync'},
                        {'source': 'erp_sync', 'target': 'notify_requester'}
                    ]
                }
            }
        )

        # 4. Workflow 2: Employee Onboarding
        WorkflowDefinition.objects.get_or_create(
            tenant=tenant,
            slug='employee-onboarding',
            defaults={
                'name': 'Employee Onboarding & Account Provisioning',
                'description': 'Automates IT identity generation, Slack/Google Workspace provisioning, and hardware logistics.',
                'trigger_type': 'event',
                'version': 1,
                'graph_schema': {
                    'nodes': [
                        {'id': 'hr_trigger', 'type': 'trigger', 'label': 'HR Hire Event Ingested'},
                        {'id': 'ldap_provision', 'type': 'http_webhook', 'label': 'IAM / SSO Account Creation'},
                        {'id': 'it_hardware', 'type': 'approval', 'label': 'IT Asset Dispatch Sign-off'},
                        {'id': 'welcome_mail', 'type': 'notification', 'label': 'Send Welcome Pack'}
                    ]
                }
            }
        )

        # 5. Seed an initial execution trace with completed steps
        if not WorkflowInstance.objects.filter(definition=wf_procure).exists():
            inst = WorkflowInstance.objects.create(
                tenant=tenant,
                definition=wf_procure,
                triggered_by=admin_user,
                status='waiting_approval',
                current_step='Executive Finance Approval',
                input_payload={
                    'po_number': 'PO-98231',
                    'amount': 12500.00,
                    'vendor': 'PostgreSQL Enterprise Services',
                    'department': 'Cloud Infrastructure'
                }
            )

            # Step 1
            StepExecution.objects.create(
                instance=inst,
                node_id='trigger_node',
                node_name='Purchase Order Submitted',
                node_type='trigger',
                status='completed',
                input_data={'po_number': 'PO-98231'},
                output_data={'status': 'accepted', 'validated': True},
                duration_ms=45,
                completed_at=timezone.now()
            )

            # Step 2
            StepExecution.objects.create(
                instance=inst,
                node_id='policy_check',
                node_name='Budget & Compliance Validation',
                node_type='condition',
                status='completed',
                input_data={'amount': 12500.00},
                output_data={'rule': 'amount > 5000', 'requires_approval': True},
                duration_ms=82,
                completed_at=timezone.now()
            )

            # Step 3 (Waiting approval)
            step3 = StepExecution.objects.create(
                instance=inst,
                node_id='approval_gate',
                node_name='Executive Finance Approval',
                node_type='approval',
                status='in_progress',
                input_data={'amount': 12500.00, 'required_role': 'manager'}
            )

            ApprovalTask.objects.create(
                instance=inst,
                step_execution=step3,
                assigned_role='manager',
                assigned_to=admin_user,
                title='Sign off PO-98231 for PostgreSQL Enterprise Services ($12,500.00)',
                description='High-value cloud infrastructure software support invoice awaiting approval.',
                status='pending'
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded FlowPulse demo data!'))
