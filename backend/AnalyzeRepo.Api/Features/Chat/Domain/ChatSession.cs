using AnalyzeRepo.Api.Data.Domain;

namespace AnalyzeRepo.Api.Features.Chat.Domain;

public sealed class ChatSession : AuditedAggregateRoot<Guid>
{
    public Guid   ConnectionId { get; private set; }
    public string RepoUrl      { get; private set; } = string.Empty;

    private readonly List<ChatMessage> _messages = new();
    public IReadOnlyList<ChatMessage> Messages => _messages.AsReadOnly();

    private ChatSession() { }

    public static ChatSession Create(Guid connectionId, string repoUrl)
    {
        return new ChatSession
        {
            Id           = Guid.NewGuid(),
            ConnectionId = connectionId,
            RepoUrl      = repoUrl,
            CreatedAt    = DateTime.UtcNow
        };
    }

    public ChatMessage AddUserMessage(string content)
    {
        var msg = ChatMessage.Create(Id, "user", content);
        _messages.Add(msg);
        return msg;
    }

    public ChatMessage AddAssistantMessage(string content)
    {
        var msg = ChatMessage.Create(Id, "assistant", content);
        _messages.Add(msg);
        return msg;
    }
}
