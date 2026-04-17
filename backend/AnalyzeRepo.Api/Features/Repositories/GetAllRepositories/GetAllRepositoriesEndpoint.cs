using AnalyzeRepo.Api.Features.Repositories;
using AnalyzeRepo.Api.Common;
using FastEndpoints;
using MediatR;

namespace AnalyzeRepo.Api.Features.Repositories.GetAllRepositories;

public class GetAllRepositoriesEndpoint : Endpoint<GetAllRepositoriesQuery, PagedResult<RepositoryDto>>
{
    private readonly IMediator _mediator;

    public GetAllRepositoriesEndpoint(IMediator mediator) => _mediator = mediator;

    public override void Configure()
    {
        Get("/repositories");
        AllowAnonymous();
        Options(x => x.WithTags("Repositories"));
        Summary(s =>
        {
            s.Summary = "Get all repositories";
            s.Description = "Retrieves a paginated list of repositories";
            s.Response<PagedResult<RepositoryDto>>(200, "Repositories retrieved successfully");
        });
    }

    public override async Task HandleAsync(GetAllRepositoriesQuery req, CancellationToken ct)
    {
        var result = await _mediator.Send(req, ct);
        Response = result;
    }
}
