using AnalyzeRepo.Api.Features.Repositories;
using FastEndpoints;
using MediatR;

namespace AnalyzeRepo.Api.Features.Repositories.DeleteRepository;

public class DeleteRepositoryEndpoint : Endpoint<DeleteRepositoryCommand>
{
    private readonly IMediator _mediator;

    public DeleteRepositoryEndpoint(IMediator mediator) => _mediator = mediator;

    public override void Configure()
    {
        Delete("/repositories/{id}");
        AllowAnonymous();
        Options(x => x.WithTags("Repositories"));
        Summary(s =>
        {
            s.Summary = "Delete a repository";
            s.Description = "Hard-deletes a repository by its ID";
            s.Response(204, "Repository deleted successfully");
            s.Response(404, "Repository not found");
        });
    }

    public override async Task HandleAsync(DeleteRepositoryCommand req, CancellationToken ct)
    {
        try
        {
            await _mediator.Send(req, ct);
            HttpContext.Response.StatusCode = 204;
        }
        catch (KeyNotFoundException)
        {
            HttpContext.Response.StatusCode = 404;
        }
    }
}
