using FastEndpoints;
using MediatR;

namespace AnalyzeRepo.Api.Features.Analysis.GetAnalysis;

public class GetAnalysisEndpoint(IMediator mediator)
    : Endpoint<GetAnalysisQuery, GetAnalysisResponse>
{
    public override void Configure()
    {
        Get("/analyses/{Id}");
        AllowAnonymous();
        Options(x => x.WithTags("Analysis"));
        Summary(s => s.Summary = "Get a specific analysis by ID");
    }

    public override async Task HandleAsync(GetAnalysisQuery req, CancellationToken ct)
    {
        var result = await mediator.Send(req, ct);
        await SendOkAsync(result, ct);
    }
}
