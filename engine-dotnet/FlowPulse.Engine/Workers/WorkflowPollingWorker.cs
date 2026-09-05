using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using FlowPulse.Engine.Data;
using FlowPulse.Engine.Services;

namespace FlowPulse.Engine.Workers
{
    public class WorkflowPollingWorker : BackgroundService
    {
        private readonly IServiceProvider _serviceProvider;
        private readonly ILogger<WorkflowPollingWorker> _logger;

        public WorkflowPollingWorker(
            IServiceProvider serviceProvider,
            ILogger<WorkflowPollingWorker> logger)
        {
            _serviceProvider = serviceProvider;
            _logger = logger;
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            _logger.LogInformation("FlowPulse .NET Workflow Polling Worker started.");

            while (!stoppingToken.IsCancellationRequested)
            {
                try
                {
                    using var scope = _serviceProvider.CreateScope();
                    var dbContext = scope.ServiceProvider.GetRequiredService<EngineDbContext>();
                    var runner = scope.ServiceProvider.GetRequiredService<IWorkflowRunner>();

                    // Check for pending instances
                    var pendingInstances = await dbContext.WorkflowInstances
                        .Where(i => i.Status == "pending")
                        .OrderBy(i => i.StartedAt)
                        .Take(5)
                        .Select(i => i.Id)
                        .ToListAsync(stoppingToken);

                    foreach (var instanceId in pendingInstances)
                    {
                        if (stoppingToken.IsCancellationRequested) break;

                        _logger.LogInformation("Worker picked up pending workflow instance {InstanceId}", instanceId);
                        try
                        {
                            await runner.ExecuteInstanceAsync(instanceId, null, stoppingToken);
                        }
                        catch (Exception ex)
                        {
                            _logger.LogError(ex, "Worker failed processing instance {InstanceId}", instanceId);
                        }
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning("Worker database check failed (will retry): {Message}", ex.Message);
                }

                await Task.Delay(TimeSpan.FromSeconds(3), stoppingToken);
            }

            _logger.LogInformation("Workflow Polling Worker stopped.");
        }
    }
}
