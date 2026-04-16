using FastEndpoints;
using MediatR;

namespace AnalyzeRepo.Api.Features.Chat.GetSession;

public class GetSessionEndpoint(IMediator mediator)
    : Endpoint<GetSessionQuery, GetSessionResponse>
{
    public override void Configure()
    {
        Get("/chat/sessions/{SessionId}");
        AllowAnonymous();
        Options(x => x.WithTags("Chat"));
        Summary(s => s.Summary = "Get a full chat session with all messages");
    }

    public override async Task HandleAsync(GetSessionQuery req, CancellationToken ct)
    {
        var result = await mediator.Send(req, ct);
        await SendOkAsync(result, ct);
    }
}
