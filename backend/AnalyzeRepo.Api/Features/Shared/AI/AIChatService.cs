using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace AnalyzeRepo.Api.Features.Shared.AI;

public sealed class AIChatService(Kernel kernel)
{
    private readonly IChatCompletionService _chat =
        kernel.GetRequiredService<IChatCompletionService>();

    public async Task<string> ChatAsync(
        string prompt,
        string? systemPrompt    = null,
        CancellationToken ct    = default)
    {
        var history = new ChatHistory();

        if (!string.IsNullOrWhiteSpace(systemPrompt))
            history.AddSystemMessage(systemPrompt);

        history.AddUserMessage(prompt);

        var results = await _chat.GetChatMessageContentsAsync(history, cancellationToken: ct);
        return results[0].Content ?? string.Empty;
    }

    public async Task<string> ChatWithHistoryAsync(
        IEnumerable<(string Role, string Content)> messages,
        CancellationToken ct = default)
    {
        var history = new ChatHistory();

        foreach (var (role, content) in messages)
        {
            switch (role.ToLowerInvariant())
            {
                case "system":    history.AddSystemMessage(content);    break;
                case "assistant": history.AddAssistantMessage(content); break;
                default:          history.AddUserMessage(content);      break;
            }
        }

        var results = await _chat.GetChatMessageContentsAsync(history, cancellationToken: ct);
        return results[0].Content ?? string.Empty;
    }
}
