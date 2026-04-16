using FastEndpoints;
using MediatR;

namespace AnalyzeRepo.Api.Features.History.DeleteHistory;

public class DeleteHistoryEndpoint(IMediator mediator)
    : EndpointWithoutRequest
{
    public override void Configure()
    {
        Delete("/history/{Id}");
        AllowAnonymous();
        Options(x => x.WithTags("History"));
        Summary(s => s.Summary = "Delete a history item (analysis) by ID");
    }

    public override async Task HandleAsync(CancellationToken ct)
    {
        var id = Route<Guid>("Id");
        await mediator.Send(new DeleteHistoryCommand(id), ct);
        await SendNoContentAsync(ct);
    }
}
