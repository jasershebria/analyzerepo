using FastEndpoints;
using MediatR;

namespace AnalyzeRepo.Api.Features.History.ListHistory;

public class ListHistoryEndpoint(IMediator mediator)
    : Endpoint<ListHistoryQuery, ListHistoryResponse>
{
    public override void Configure()
    {
        Get("/history");
        AllowAnonymous();
        Options(x => x.WithTags("History"));
        Summary(s => s.Summary = "List all past analyses with optional search and pagination");
    }

    public override async Task HandleAsync(ListHistoryQuery req, CancellationToken ct)
    {
        var result = await mediator.Send(req, ct);
        await SendOkAsync(result, ct);
    }
}
