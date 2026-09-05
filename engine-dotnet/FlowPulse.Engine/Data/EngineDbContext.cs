using Microsoft.EntityFrameworkCore;
using FlowPulse.Engine.Models;

namespace FlowPulse.Engine.Data
{
    public class EngineDbContext : DbContext
    {
        public EngineDbContext(DbContextOptions<EngineDbContext> options) : base(options)
        {
        }

        public DbSet<WorkflowDefinitionEntity> WorkflowDefinitions => Set<WorkflowDefinitionEntity>();
        public DbSet<WorkflowInstanceEntity> WorkflowInstances => Set<WorkflowInstanceEntity>();
        public DbSet<StepExecutionEntity> StepExecutions => Set<StepExecutionEntity>();
        public DbSet<ApprovalTaskEntity> ApprovalTasks => Set<ApprovalTaskEntity>();

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            modelBuilder.Entity<WorkflowDefinitionEntity>(entity =>
            {
                entity.ToTable("workflow_definitions");
                entity.HasKey(e => e.Id);
            });

            modelBuilder.Entity<WorkflowInstanceEntity>(entity =>
            {
                entity.ToTable("workflow_instances");
                entity.HasKey(e => e.Id);
                entity.HasOne(e => e.Definition)
                      .WithMany(d => d.Instances)
                      .HasForeignKey(e => e.DefinitionId)
                      .OnDelete(DeleteBehavior.Cascade);

                entity.HasMany(e => e.StepExecutions)
                      .WithOne(s => s.Instance)
                      .HasForeignKey(s => s.InstanceId)
                      .OnDelete(DeleteBehavior.Cascade);

                entity.HasMany(e => e.ApprovalTasks)
                      .WithOne(a => a.Instance)
                      .HasForeignKey(a => a.InstanceId)
                      .OnDelete(DeleteBehavior.Cascade);
            });

            modelBuilder.Entity<StepExecutionEntity>(entity =>
            {
                entity.ToTable("step_executions");
                entity.HasKey(e => e.Id);
            });

            modelBuilder.Entity<ApprovalTaskEntity>(entity =>
            {
                entity.ToTable("approval_tasks");
                entity.HasKey(e => e.Id);
            });
        }
    }
}
