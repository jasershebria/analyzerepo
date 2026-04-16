using FastEndpoints;
using MediatR;

namespace AnalyzeRepo.Api.Features.Repository.GetRepository;

public class GetRepositoryEndpoint(IMediator mediator)
    : Endpoint<GetRepositoryQuery, GetRepositoryResponse>
{
    public override void Configure()
    {
        Get("/repositories/{Id}");
        AllowAnonymous();
        Options(x => x.WithTags("Repository"));
        Summary(s => s.Summary = "Get a repository connection by ID");
    }

    public override async Task HandleAsync(GetRepositoryQuery req, CancellationToken ct)
    {
        var result = await mediator.Send(req, ct);
        await SendOkAsync(result, ct);
    }
}
