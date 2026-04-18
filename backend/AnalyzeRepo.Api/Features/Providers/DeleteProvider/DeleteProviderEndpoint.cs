using FastEndpoints;
using MediatR;

namespace AnalyzeRepo.Api.Features.Providers.DeleteProvider;

public class DeleteProviderEndpoint : Endpoint<DeleteProviderCommand>
{
    private readonly IMediator _mediator;

    public DeleteProviderEndpoint(IMediator mediator) => _mediator = mediator;

    public override void Configure()
    {
        Delete("/providers/{id}");
        AllowAnonymous();
        Options(x => x.WithTags("Providers"));
        Summary(s =>
        {
            s.Summary = "Delete a provider";
            s.Response(204, "Provider deleted successfully");
            s.Response(404, "Provider not found");
        });
    }

    public override async Task HandleAsync(DeleteProviderCommand req, CancellationToken ct)
    {
        await _mediator.Send(req, ct);
        await SendNoContentAsync(ct);
    }
}
