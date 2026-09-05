using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using FlowPulse.Engine.Services;

namespace FlowPulse.Engine.Controllers
{
    [ApiController]
    [Route("api/v1/engine")]
    public class EngineController : ControllerBase
    {
        private readonly IWorkflowRunner _workflowRunner;
        private readonly ILogger<EngineController> _logger;

        public EngineController(IWorkflowRunner workflowRunner, ILogger<EngineController> logger)
        {
            _workflowRunner = workflowRunner;
            _logger = logger;
        }

        [HttpGet("health")]
        public IActionResult Health()
        {
            return Ok(new
            {
                status = "healthy",
                engine = "FlowPulse C# .NET Core 8.0 State Engine",
                timestamp = DateTime.UtcNow,
                environment = Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT") ?? "Development",
                allocatedMemoryBytes = GC.GetTotalMemory(false)
            });
        }

        [HttpPost("execute")]
        public async Task<IActionResult> Execute([FromBody] ExecuteRequest request)
        {
            if (request.InstanceId == Guid.Empty)
            {
                return BadRequest(new { error = "InstanceId is required." });
            }

            try
            {
                var instance = await _workflowRunner.ExecuteInstanceAsync(request.InstanceId, request.Payload);
                return Ok(new
                {
                    instanceId = instance.Id,
                    status = instance.Status,
                    currentStep = instance.CurrentStep,
                    completedAt = instance.CompletedAt
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error executing workflow instance {InstanceId}", request.InstanceId);
                return StatusCode(500, new { error = ex.Message });
            }
        }

        [HttpPost("resume")]
        public async Task<IActionResult> Resume([FromBody] ResumeRequest request)
        {
            if (request.TaskId == Guid.Empty)
            {
                return BadRequest(new { error = "TaskId is required." });
            }

            try
            {
                var instance = await _workflowRunner.ResumeWorkflowAsync(
                    request.TaskId,
                    request.Decision,
                    request.DecisionNote ?? string.Empty
                );

                if (instance == null)
                {
                    return NotFound(new { error = "Approval task not found or has no linked workflow instance." });
                }

                return Ok(new
                {
                    instanceId = instance.Id,
                    status = instance.Status,
                    currentStep = instance.CurrentStep,
                    completedAt = instance.CompletedAt
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error resuming approval task {TaskId}", request.TaskId);
                return StatusCode(500, new { error = ex.Message });
            }
        }
    }

    public class ExecuteRequest
    {
        public Guid InstanceId { get; set; }
        public Dictionary<string, object>? Payload { get; set; }
    }

    public class ResumeRequest
    {
        public Guid TaskId { get; set; }
        public string Decision { get; set; } = "approved"; // approved or rejected
        public string? DecisionNote { get; set; }
    }
}
