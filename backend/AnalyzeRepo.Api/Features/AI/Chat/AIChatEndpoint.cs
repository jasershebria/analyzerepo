using AnalyzeRepo.Api.Features.Shared.AI;
using FastEndpoints;

namespace AnalyzeRepo.Api.Features.AI.Chat;

public sealed record AIChatRequest(
    string  Prompt,
    string? SystemPrompt = null);

public sealed record AIChatResponse(string Reply);

public sealed class AIChatEndpoint(AIChatService ai)
    : Endpoint<AIChatRequest, AIChatResponse>
{
    public override void Configure()
    {
        Post("/ai/chat");
        AllowAnonymous();
        Summary(s =>
        {
            s.Summary     = "Send a prompt to Claude via Semantic Kernel";
            s.Description = "Returns the model's reply. Swap the provider in AIServiceExtensions without changing this endpoint.";
        });
    }

    public override async Task HandleAsync(AIChatRequest req, CancellationToken ct)
    {
        var reply = await ai.ChatAsync(req.Prompt, req.SystemPrompt, ct);
        await SendOkAsync(new AIChatResponse(reply), ct);
    }
}
