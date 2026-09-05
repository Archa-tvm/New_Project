using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using FlowPulse.Engine.Models;

namespace FlowPulse.Engine.Services
{
    public interface IWorkflowRunner
    {
        Task<WorkflowInstanceEntity> ExecuteInstanceAsync(
            Guid instanceId,
            Dictionary<string, object>? initialPayload = null,
            CancellationToken cancellationToken = default
        );

        Task<WorkflowInstanceEntity?> ResumeWorkflowAsync(
            Guid approvalTaskId,
            string decision,
            string decisionNote,
            CancellationToken cancellationToken = default
        );
    }
}
