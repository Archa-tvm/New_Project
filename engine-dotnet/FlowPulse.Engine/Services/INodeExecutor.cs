using System.Text.Json;
using FlowPulse.Engine.Models;

namespace FlowPulse.Engine.Services
{
    public class NodeExecutionResult
    {
        public bool Success { get; set; } = true;
        public string? NextNodeId { get; set; }
        public bool SuspendWorkflow { get; set; } = false; // Used for Human-in-the-loop approvals
        public Dictionary<string, object> OutputData { get; set; } = new();
        public string? ErrorMessage { get; set; }
    }

    public interface INodeExecutor
    {
        string NodeType { get; }
        Task<NodeExecutionResult> ExecuteAsync(
            WorkflowNodeSchema node,
            WorkflowInstanceEntity instance,
            Dictionary<string, object> contextPayload,
            CancellationToken cancellationToken = default
        );
    }
}
