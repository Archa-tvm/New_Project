using Microsoft.AspNetCore.Builder;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using FlowPulse.Engine.Data;
using FlowPulse.Engine.Services;
using FlowPulse.Engine.Workers;

var builder = WebApplication.CreateBuilder(args);

// Configure Database Connection
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");

if (!string.IsNullOrEmpty(connectionString) && !connectionString.Contains("localhost_placeholder"))
{
    builder.Services.AddDbContext<EngineDbContext>(options =>
        options.UseNpgsql(connectionString));
}
else
{
    builder.Services.AddDbContext<EngineDbContext>(options =>
        options.UseInMemoryDatabase("FlowPulseInMemoryDb"));
}

// Register HTTP Client Factory
builder.Services.AddHttpClient();

// Register Node Executors
builder.Services.AddTransient<INodeExecutor, TriggerNodeExecutor>();
builder.Services.AddTransient<INodeExecutor, ConditionNodeExecutor>();
builder.Services.AddTransient<INodeExecutor, HttpWebhookNodeExecutor>();
builder.Services.AddTransient<INodeExecutor, ApprovalNodeExecutor>();
builder.Services.AddTransient<INodeExecutor, NotificationNodeExecutor>();

// Register Workflow Runner Service
builder.Services.AddScoped<IWorkflowRunner, WorkflowRunner>();

// Register Background Polling Worker
builder.Services.AddHostedService<WorkflowPollingWorker>();

// Add Controllers and Swagger
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin().AllowAnyHeader().AllowAnyMethod();
    });
});

var app = builder.Build();

// Configure HTTP pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(c =>
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "FlowPulse Engine API v1");
        c.RoutePrefix = "swagger";
    });
}

app.UseCors();
app.UseAuthorization();
app.MapControllers();

app.Run();
