using AnalyzeRepo.Api.Data.Application.Behaviors;
using AnalyzeRepo.Api.Data.Infrastructure;
using AnalyzeRepo.Api.Features.Providers.Infrastructure.Plugins;
using AnalyzeRepo.Api.Features.Shared.AI;
using AnalyzeRepo.Api.Services;
using FastEndpoints;
using FastEndpoints.Swagger;
using MediatR;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// ── CORS ──────────────────────────────────────────────────────────────────────
builder.Services.AddCors(options =>
    options.AddDefaultPolicy(policy =>
        policy.WithOrigins("http://localhost:4200")
              .AllowAnyHeader()
              .AllowAnyMethod()));

// ── Data / EF Core ────────────────────────────────────────────────────────────
builder.Services.AddDataServices(builder.Configuration);

// ── MediatR + Pipeline Behaviors ─────────────────────────────────────────────
builder.Services.AddMediatR(cfg =>
{
    cfg.RegisterServicesFromAssemblyContaining<Program>();
    cfg.AddBehavior(typeof(IPipelineBehavior<,>), typeof(LoggingBehavior<,>));
    cfg.AddBehavior(typeof(IPipelineBehavior<,>), typeof(ValidationBehavior<,>));
});

// ── FluentValidation — register validators for MediatR pipeline ──────────────
builder.Services.Scan(scan => scan
    .FromAssemblyOf<Program>()
    .AddClasses(c => c.AssignableTo(typeof(FluentValidation.IValidator<>)))
    .AsImplementedInterfaces()
    .WithTransientLifetime());

// ── External Services ─────────────────────────────────────────────────────────
builder.Services.Configure<LlmOptions>(
    builder.Configuration.GetSection(LlmOptions.Section));
builder.Services.AddHttpClient<ILlmService, OpenAiLlmService>();

// ── Semantic Kernel / AI ──────────────────────────────────────────────────────
builder.Services.AddAIServices(builder.Configuration);


// ── Plugin system ─────────────────────────────────────────────────────────────
builder.Services.AddProviderPlugins();

// ── FastEndpoints ─────────────────────────────────────────────────────────────
builder.Services.AddFastEndpoints();

// ── Swagger (FastEndpoints built-in NSwag) ────────────────────────────────────
builder.Services.SwaggerDocument(o =>
{
    o.DocumentSettings = s =>
    {
        s.Title   = "AnalyzeRepo API";
        s.Version = "v1";
    };
});

// ── Problem Details ───────────────────────────────────────────────────────────
builder.Services.AddProblemDetails();

var app = builder.Build();

// ── Apply EF Core migrations on startup ───────────────────────────────────────
{
    using var scope = app.Services.CreateScope();
    var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
    await db.Database.MigrateAsync();
}

app.UseCors();
app.UseExceptionHandler();

app.UseFastEndpoints(c =>
{
    c.Endpoints.RoutePrefix = "api";
    c.Errors.UseProblemDetails();
    c.Serializer.Options.Converters.Add(
        new System.Text.Json.Serialization.JsonStringEnumConverter());
});

app.UseSwaggerGen();

app.Run();
