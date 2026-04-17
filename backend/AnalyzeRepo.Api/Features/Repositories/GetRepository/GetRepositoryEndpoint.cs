using AnalyzeRepo.Api.Features.Repositories;
using FastEndpoints;
using FluentValidation;
using MediatR;

namespace AnalyzeRepo.Api.Features.Repositories.GetRepository;

public class GetRepositoryEndpoint : Endpoint<GetRepositoryQuery, GetRepositoryResponse?>
{
    private readonly IMediator _mediator;

    public GetRepositoryEndpoint(IMediator mediator) => _mediator = mediator;

    public override void Configure()
    {
        Get("/repositories/{id}");
        AllowAnonymous();
        Options(x => x.WithTags("Repositories"));
        Summary(s =>
        {
            s.Summary = "Get a repository by ID";
            s.Description = "Retrieves a repository by its unique identifier";
            s.Response<GetRepositoryResponse>(200, "Repository found");
            s.Response(404, "Repository not found");
        });
    }

    public override async Task HandleAsync(GetRepositoryQuery req, CancellationToken ct)
    {
        var result = await _mediator.Send(req, ct);
        if (result == null) { HttpContext.Response.StatusCode = 404; return; }
        Response = result;
    }
}

public class GetRepositoryValidator : Validator<GetRepositoryQuery>
{
    public GetRepositoryValidator()
    {
        RuleFor(x => x.Id).NotEmpty();
    }
}
