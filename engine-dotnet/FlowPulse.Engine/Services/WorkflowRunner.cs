using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using FlowPulse.Engine.Data;
using FlowPulse.Engine.Models;

namespace FlowPulse.Engine.Services
{
    public class WorkflowRunner : IWorkflowRunner
    {
        private readonly EngineDbContext _dbContext;
        private readonly IEnumerable<INodeExecutor> _executors;
        private readonly ILogger<WorkflowRunner> _logger;

        public WorkflowRunner(
            EngineDbContext dbContext,
            IEnumerable<INodeExecutor> executors,
            ILogger<WorkflowRunner> logger)
        {
            _dbContext = dbContext;
            _executors = executors;
            _logger = logger;
        }

        public async Task<WorkflowInstanceEntity> ExecuteInstanceAsync(
            Guid instanceId,
            Dictionary<string, object>? initialPayload = null,
            CancellationToken cancellationToken = default)
        {
            var instance = await _dbContext.WorkflowInstances
                .Include(i => i.Definition)
                .Include(i => i.StepExecutions)
                .FirstOrDefaultAsync(i => i.Id == instanceId, cancellationToken);

            if (instance == null)
            {
                throw new InvalidOperationException($"Workflow instance {instanceId} not found in database.");
            }

            if (instance.Definition == null)
            {
                throw new InvalidOperationException($"Workflow definition missing for instance {instanceId}.");
            }

            _logger.LogInformation("Starting execution for Workflow Instance {InstanceId} ({DefinitionName})",
                instance.Id, instance.Definition.Name);

            instance.Status = "running";
            instance.StartedAt = DateTime.UtcNow;
            await _dbContext.SaveChangesAsync(cancellationToken);

            var contextPayload = new Dictionary<string, object>();
            if (!string.IsNullOrWhiteSpace(instance.InputPayloadJson) && instance.InputPayloadJson != "{}")
            {
                try
                {
                    var parsed = JsonSerializer.Deserialize<Dictionary<string, object>>(instance.InputPayloadJson);
                    if (parsed != null)
                    {
                        foreach (var kvp in parsed) contextPayload[kvp.Key] = kvp.Value;
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Failed to parse InputPayloadJson for instance {InstanceId}", instance.Id);
                }
            }

            if (initialPayload != null)
            {
                foreach (var kvp in initialPayload) contextPayload[kvp.Key] = kvp.Value;
            }

            // Parse Schema
            WorkflowGraphSchema graph;
            try
            {
                graph = JsonSerializer.Deserialize<WorkflowGraphSchema>(
                    instance.Definition.GraphSchemaJson,
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
                ) ?? new WorkflowGraphSchema();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Invalid graph schema JSON in definition {DefinitionId}", instance.DefinitionId);
                instance.Status = "failed";
                instance.ErrorMessage = $"Failed to parse workflow blueprint schema: {ex.Message}";
                instance.CompletedAt = DateTime.UtcNow;
                await _dbContext.SaveChangesAsync(cancellationToken);
                return instance;
            }

            if (graph.Nodes.Count == 0)
            {
                instance.Status = "completed";
                instance.CompletedAt = DateTime.UtcNow;
                await _dbContext.SaveChangesAsync(cancellationToken);
                return instance;
            }

            // Start with trigger node, or first node
            var currentNode = graph.Nodes.FirstOrDefault(n => n.Type == "trigger") ?? graph.Nodes.First();

            while (currentNode != null)
            {
                instance.CurrentStep = currentNode.Label ?? currentNode.Id;
                _logger.LogInformation("Executing node {NodeId} ({NodeType}) for instance {InstanceId}",
                    currentNode.Id, currentNode.Type, instance.Id);

                var executor = _executors.FirstOrDefault(e => e.NodeType.Equals(currentNode.Type, StringComparison.OrdinalIgnoreCase))
                               ?? _executors.FirstOrDefault(e => e.NodeType == "notification"); // safe default

                var sw = Stopwatch.StartNew();
                var stepExecution = new StepExecutionEntity
                {
                    Id = Guid.NewGuid(),
                    InstanceId = instance.Id,
                    NodeId = currentNode.Id,
                    NodeName = currentNode.Label ?? currentNode.Id,
                    NodeType = currentNode.Type,
                    Status = "in_progress",
                    InputDataJson = JsonSerializer.Serialize(contextPayload),
                    StartedAt = DateTime.UtcNow
                };

                _dbContext.StepExecutions.Add(stepExecution);
                await _dbContext.SaveChangesAsync(cancellationToken);

                NodeExecutionResult result;
                if (executor != null)
                {
                    result = await executor.ExecuteAsync(currentNode, instance, contextPayload, cancellationToken);
                }
                else
                {
                    result = new NodeExecutionResult { Success = true };
                }

                sw.Stop();
                stepExecution.DurationMs = sw.ElapsedMilliseconds;
                stepExecution.CompletedAt = DateTime.UtcNow;
                stepExecution.OutputDataJson = JsonSerializer.Serialize(result.OutputData);

                // Update context payload with output data
                foreach (var kvp in result.OutputData)
                {
                    contextPayload[kvp.Key] = kvp.Value;
                }

                if (!result.Success)
                {
                    stepExecution.Status = "failed";
                    stepExecution.ErrorMessage = result.ErrorMessage ?? "Node execution reported failure";
                    instance.Status = "failed";
                    instance.ErrorMessage = stepExecution.ErrorMessage;
                    instance.CompletedAt = DateTime.UtcNow;
                    instance.OutputPayloadJson = JsonSerializer.Serialize(contextPayload);
                    await _dbContext.SaveChangesAsync(cancellationToken);
                    return instance;
                }

                stepExecution.Status = "completed";
                await _dbContext.SaveChangesAsync(cancellationToken);

                if (result.SuspendWorkflow)
                {
                    // Suspended at human approval step
                    instance.Status = "waiting_approval";
                    instance.OutputPayloadJson = JsonSerializer.Serialize(contextPayload);
                    await _dbContext.SaveChangesAsync(cancellationToken);
                    _logger.LogInformation("Instance {InstanceId} successfully suspended at step '{CurrentStep}'", instance.Id, instance.CurrentStep);
                    return instance;
                }

                // Determine next node
                WorkflowNodeSchema? nextNode = null;
                if (!string.IsNullOrEmpty(result.NextNodeId))
                {
                    nextNode = graph.Nodes.FirstOrDefault(n => n.Id == result.NextNodeId);
                }
                else
                {
                    var edge = graph.Edges.FirstOrDefault(e => e.Source == currentNode.Id);
                    if (edge != null)
                    {
                        nextNode = graph.Nodes.FirstOrDefault(n => n.Id == edge.Target);
                    }
                    else
                    {
                        // Linear fallback: take adjacent node in list
                        int idx = graph.Nodes.IndexOf(currentNode);
                        if (idx >= 0 && idx + 1 < graph.Nodes.Count)
                        {
                            nextNode = graph.Nodes[idx + 1];
                        }
                    }
                }

                currentNode = nextNode;
            }

            // All steps executed to completion
            instance.Status = "completed";
            instance.CompletedAt = DateTime.UtcNow;
            instance.CurrentStep = "End";
            instance.OutputPayloadJson = JsonSerializer.Serialize(contextPayload);
            await _dbContext.SaveChangesAsync(cancellationToken);

            _logger.LogInformation("Workflow Instance {InstanceId} completed successfully.", instance.Id);
            return instance;
        }

        public async Task<WorkflowInstanceEntity?> ResumeWorkflowAsync(
            Guid approvalTaskId,
            string decision,
            string decisionNote,
            CancellationToken cancellationToken = default)
        {
            var task = await _dbContext.ApprovalTasks
                .Include(a => a.Instance)
                    .ThenInclude(i => i!.Definition)
                .FirstOrDefaultAsync(a => a.Id == approvalTaskId, cancellationToken);

            if (task == null || task.Instance == null)
            {
                _logger.LogWarning("Approval task {TaskId} not found or has no instance", approvalTaskId);
                return null;
            }

            var instance = task.Instance;
            task.Status = decision.ToLowerInvariant();
            task.DecisionNote = decisionNote;
            task.DecidedAt = DateTime.UtcNow;

            if (decision.Equals("rejected", StringComparison.OrdinalIgnoreCase))
            {
                instance.Status = "failed";
                instance.ErrorMessage = $"Workflow rejected by human approver: {decisionNote}";
                instance.CompletedAt = DateTime.UtcNow;
                await _dbContext.SaveChangesAsync(cancellationToken);
                return instance;
            }

            // Approved: Resume execution from next step
            instance.Status = "running";
            await _dbContext.SaveChangesAsync(cancellationToken);

            // Re-invoke execution to progress remaining steps
            return await ExecuteInstanceAsync(instance.Id, null, cancellationToken);
        }
    }
}
