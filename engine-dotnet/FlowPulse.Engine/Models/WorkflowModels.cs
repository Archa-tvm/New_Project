using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace FlowPulse.Engine.Models
{
    [Table("workflow_definitions")]
    public class WorkflowDefinitionEntity
    {
        [Key]
        [Column("id")]
        public Guid Id { get; set; }

        [Column("tenant_id")]
        public Guid TenantId { get; set; }

        [Column("name")]
        public string Name { get; set; } = string.Empty;

        [Column("slug")]
        public string Slug { get; set; } = string.Empty;

        [Column("description")]
        public string Description { get; set; } = string.Empty;

        [Column("trigger_type")]
        public string TriggerType { get; set; } = "manual";

        [Column("graph_schema", TypeName = "jsonb")]
        public string GraphSchemaJson { get; set; } = "{}";

        [Column("version")]
        public int Version { get; set; } = 1;

        [Column("is_active")]
        public bool IsActive { get; set; } = true;

        [Column("created_at")]
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        [Column("updated_at")]
        public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

        [JsonIgnore]
        public List<WorkflowInstanceEntity> Instances { get; set; } = new();
    }

    [Table("workflow_instances")]
    public class WorkflowInstanceEntity
    {
        [Key]
        [Column("id")]
        public Guid Id { get; set; }

        [Column("tenant_id")]
        public Guid TenantId { get; set; }

        [Column("definition_id")]
        public Guid DefinitionId { get; set; }

        [ForeignKey(nameof(DefinitionId))]
        public WorkflowDefinitionEntity? Definition { get; set; }

        [Column("triggered_by_id")]
        public int? TriggeredById { get; set; }

        [Column("status")]
        public string Status { get; set; } = "pending"; // pending, running, waiting_approval, completed, failed, cancelled

        [Column("current_step")]
        public string CurrentStep { get; set; } = string.Empty;

        [Column("input_payload", TypeName = "jsonb")]
        public string InputPayloadJson { get; set; } = "{}";

        [Column("output_payload", TypeName = "jsonb")]
        public string OutputPayloadJson { get; set; } = "{}";

        [Column("error_message")]
        public string ErrorMessage { get; set; } = string.Empty;

        [Column("started_at")]
        public DateTime StartedAt { get; set; } = DateTime.UtcNow;

        [Column("completed_at")]
        public DateTime? CompletedAt { get; set; }

        public List<StepExecutionEntity> StepExecutions { get; set; } = new();
        public List<ApprovalTaskEntity> ApprovalTasks { get; set; } = new();
    }

    [Table("step_executions")]
    public class StepExecutionEntity
    {
        [Key]
        [Column("id")]
        public Guid Id { get; set; } = Guid.NewGuid();

        [Column("instance_id")]
        public Guid InstanceId { get; set; }

        [ForeignKey(nameof(InstanceId))]
        [JsonIgnore]
        public WorkflowInstanceEntity? Instance { get; set; }

        [Column("node_id")]
        public string NodeId { get; set; } = string.Empty;

        [Column("node_name")]
        public string NodeName { get; set; } = string.Empty;

        [Column("node_type")]
        public string NodeType { get; set; } = "condition"; // trigger, condition, http_webhook, approval, notification, transform

        [Column("status")]
        public string Status { get; set; } = "pending"; // pending, in_progress, completed, failed, skipped

        [Column("input_data", TypeName = "jsonb")]
        public string InputDataJson { get; set; } = "{}";

        [Column("output_data", TypeName = "jsonb")]
        public string OutputDataJson { get; set; } = "{}";

        [Column("error_message")]
        public string ErrorMessage { get; set; } = string.Empty;

        [Column("duration_ms")]
        public long DurationMs { get; set; } = 0;

        [Column("started_at")]
        public DateTime StartedAt { get; set; } = DateTime.UtcNow;

        [Column("completed_at")]
        public DateTime? CompletedAt { get; set; }
    }

    [Table("approval_tasks")]
    public class ApprovalTaskEntity
    {
        [Key]
        [Column("id")]
        public Guid Id { get; set; } = Guid.NewGuid();

        [Column("instance_id")]
        public Guid InstanceId { get; set; }

        [ForeignKey(nameof(InstanceId))]
        [JsonIgnore]
        public WorkflowInstanceEntity? Instance { get; set; }

        [Column("step_execution_id")]
        public Guid? StepExecutionId { get; set; }

        [Column("assigned_role")]
        public string AssignedRole { get; set; } = "manager";

        [Column("assigned_to_id")]
        public int? AssignedToId { get; set; }

        [Column("title")]
        public string Title { get; set; } = string.Empty;

        [Column("description")]
        public string Description { get; set; } = string.Empty;

        [Column("status")]
        public string Status { get; set; } = "pending"; // pending, approved, rejected

        [Column("decision_by_id")]
        public int? DecisionById { get; set; }

        [Column("decision_note")]
        public string DecisionNote { get; set; } = string.Empty;

        [Column("decided_at")]
        public DateTime? DecidedAt { get; set; }

        [Column("created_at")]
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    }

    // Graph Schema Serialization Models
    public class WorkflowGraphSchema
    {
        public List<WorkflowNodeSchema> Nodes { get; set; } = new();
        public List<WorkflowEdgeSchema> Edges { get; set; } = new();
    }

    public class WorkflowNodeSchema
    {
        public string Id { get; set; } = string.Empty;
        public string Type { get; set; } = string.Empty;
        public string Label { get; set; } = string.Empty;
        public JsonElement? Config { get; set; }
    }

    public class WorkflowEdgeSchema
    {
        public string Source { get; set; } = string.Empty;
        public string Target { get; set; } = string.Empty;
        public string? Condition { get; set; }
    }
}
