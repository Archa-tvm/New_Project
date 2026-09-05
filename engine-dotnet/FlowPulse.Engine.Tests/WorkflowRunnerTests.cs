using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging.Abstractions;
using FlowPulse.Engine.Data;
using FlowPulse.Engine.Models;
using FlowPulse.Engine.Services;
using Xunit;

namespace FlowPulse.Engine.Tests
{
    public class WorkflowRunnerTests
    {
        private EngineDbContext CreateInMemoryDbContext()
        {
            var options = new DbContextOptionsBuilder<EngineDbContext>()
                .UseInMemoryDatabase(Guid.NewGuid().ToString())
                .Options;
            return new EngineDbContext(options);
        }

        [Fact]
        public async Task ConditionNodeExecutor_EvaluatesGreaterThan_Correctly()
        {
            var executor = new ConditionNodeExecutor(NullLogger<ConditionNodeExecutor>.Instance);
            var node = new WorkflowNodeSchema
            {
                Id = "cond_1",
                Type = "condition",
                Label = "Check Amount",
                Config = JsonDocument.Parse("{\"field\":\"amount\",\"operator\":\"greater_than\",\"threshold\":5000,\"on_true\":\"step_high\",\"on_false\":\"step_low\"}").RootElement
            };

            var instance = new WorkflowInstanceEntity { Id = Guid.NewGuid() };
            var payloadHigh = new Dictionary<string, object> { ["amount"] = 8000 };

            var res = await executor.ExecuteAsync(node, instance, payloadHigh);

            Assert.True(res.Success);
            Assert.Equal("step_high", res.NextNodeId);
            Assert.True((bool)res.OutputData["condition_met"]);
        }

        [Fact]
        public async Task WorkflowRunner_EndToEnd_LinearExecution_CompletesSuccessfully()
        {
            using var db = CreateInMemoryDbContext();

            var executors = new INodeExecutor[]
            {
                new TriggerNodeExecutor(),
                new ConditionNodeExecutor(NullLogger<ConditionNodeExecutor>.Instance),
                new NotificationNodeExecutor(NullLogger<NotificationNodeExecutor>.Instance)
            };

            var runner = new WorkflowRunner(db, executors, NullLogger<WorkflowRunner>.Instance);

            var tenantId = Guid.NewGuid();
            var definition = new WorkflowDefinitionEntity
            {
                Id = Guid.NewGuid(),
                TenantId = tenantId,
                Name = "Simple Purchase Pipeline",
                Slug = "simple-purchase",
                GraphSchemaJson = JsonSerializer.Serialize(new WorkflowGraphSchema
                {
                    Nodes = new List<WorkflowNodeSchema>
                    {
                        new() { Id = "start", Type = "trigger", Label = "Start" },
                        new() { Id = "cond", Type = "condition", Label = "Amount Check", Config = JsonDocument.Parse("{\"field\":\"amount\",\"operator\":\"greater_than\",\"threshold\":1000,\"on_true\":\"notify\",\"on_false\":\"notify\"}").RootElement },
                        new() { Id = "notify", Type = "notification", Label = "Send Notification" }
                    },
                    Edges = new List<WorkflowEdgeSchema>
                    {
                        new() { Source = "start", Target = "cond" },
                        new() { Source = "cond", Target = "notify" }
                    }
                })
            };

            var instance = new WorkflowInstanceEntity
            {
                Id = Guid.NewGuid(),
                TenantId = tenantId,
                DefinitionId = definition.Id,
                Definition = definition,
                Status = "pending",
                InputPayloadJson = "{\"amount\": 2500}"
            };

            db.WorkflowDefinitions.Add(definition);
            db.WorkflowInstances.Add(instance);
            await db.SaveChangesAsync();

            var result = await runner.ExecuteInstanceAsync(instance.Id);

            Assert.Equal("completed", result.Status);
            Assert.NotNull(result.CompletedAt);

            var steps = await db.StepExecutions.Where(s => s.InstanceId == instance.Id).ToListAsync();
            Assert.Equal(3, steps.Count);
        }

        [Fact]
        public async Task WorkflowRunner_ApprovalGate_SuspendsWorkflow()
        {
            using var db = CreateInMemoryDbContext();

            var executors = new INodeExecutor[]
            {
                new TriggerNodeExecutor(),
                new ApprovalNodeExecutor(db, NullLogger<ApprovalNodeExecutor>.Instance)
            };

            var runner = new WorkflowRunner(db, executors, NullLogger<WorkflowRunner>.Instance);

            var tenantId = Guid.NewGuid();
            var definition = new WorkflowDefinitionEntity
            {
                Id = Guid.NewGuid(),
                TenantId = tenantId,
                Name = "Approval Workflow",
                Slug = "approval-wf",
                GraphSchemaJson = JsonSerializer.Serialize(new WorkflowGraphSchema
                {
                    Nodes = new List<WorkflowNodeSchema>
                    {
                        new() { Id = "start", Type = "trigger", Label = "Start" },
                        new() { Id = "approval", Type = "approval", Label = "Manager Sign-off" }
                    },
                    Edges = new List<WorkflowEdgeSchema>
                    {
                        new() { Source = "start", Target = "approval" }
                    }
                })
            };

            var instance = new WorkflowInstanceEntity
            {
                Id = Guid.NewGuid(),
                TenantId = tenantId,
                DefinitionId = definition.Id,
                Definition = definition,
                Status = "pending"
            };

            db.WorkflowDefinitions.Add(definition);
            db.WorkflowInstances.Add(instance);
            await db.SaveChangesAsync();

            var result = await runner.ExecuteInstanceAsync(instance.Id);

            Assert.Equal("waiting_approval", result.Status);
            var tasks = await db.ApprovalTasks.Where(a => a.InstanceId == instance.Id).ToListAsync();
            Assert.Single(tasks);
            Assert.Equal("pending", tasks[0].Status);
        }
    }
}
