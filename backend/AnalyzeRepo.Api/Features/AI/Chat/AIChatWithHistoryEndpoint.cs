using AnalyzeRepo.Api.Features.Shared.AI;
using FastEndpoints;

namespace AnalyzeRepo.Api.Features.AI.Chat;

public sealed record ChatMessageDto(string Role, string Content);

public sealed record AIChatWithHistoryRequest(
    IReadOnlyList<ChatMessageDto> Messages,
    string? SystemPrompt = null);

public sealed class AIChatWithHistoryEndpoint(AIChatService ai)
    : Endpoint<AIChatWithHistoryRequest, AIChatResponse>
{
    public override void Configure()
    {
        Post("/ai/chat/history");
        AllowAnonymous();
        Summary(s =>
        {
            s.Summary     = "Send a multi-turn conversation to Claude via Semantic Kernel";
            s.Description = "Accepts a full message history and returns the model's next reply.";
        });
    }

    public override async Task HandleAsync(AIChatWithHistoryRequest req, CancellationToken ct)
    {
        var history = req.Messages
            .Select(m => (m.Role, m.Content))
            .ToList();

        if (!string.IsNullOrWhiteSpace(req.SystemPrompt))
            history.Insert(0, ("system", req.SystemPrompt));

        var reply = await ai.ChatWithHistoryAsync(history, ct);
        await SendOkAsync(new AIChatResponse(reply), ct);
    }
}
