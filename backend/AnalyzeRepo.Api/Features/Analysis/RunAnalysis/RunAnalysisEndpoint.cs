using FastEndpoints;
using FluentValidation;
using MediatR;

namespace AnalyzeRepo.Api.Features.Analysis.RunAnalysis;

public class RunAnalysisEndpoint(IMediator mediator)
    : Endpoint<RunAnalysisCommand, RunAnalysisResponse>
{
    public override void Configure()
    {
        Post("/analyses");
        AllowAnonymous();
        Options(x => x.WithTags("Analysis"));
        Summary(s =>
        {
            s.Summary     = "Run an analysis on a connected repository";
            s.Description = "Sends a query to the AI and returns a Mermaid flowchart and step breakdown";
        });
    }

    public override async Task HandleAsync(RunAnalysisCommand req, CancellationToken ct)
    {
        var result = await mediator.Send(req, ct);
        await SendOkAsync(result, ct);
    }
}

public class RunAnalysisValidator : Validator<RunAnalysisCommand>
{
    public RunAnalysisValidator()
    {
        RuleFor(x => x.ConnectionId).NotEmpty().WithMessage("ConnectionId is required.");
        RuleFor(x => x.Query)
            .NotEmpty().WithMessage("Query is required.")
            .MaximumLength(2000).WithMessage("Query must not exceed 2000 characters.");
    }
}
