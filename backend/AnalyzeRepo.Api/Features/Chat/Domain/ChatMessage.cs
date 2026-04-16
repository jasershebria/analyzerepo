using AnalyzeRepo.Api.Data.Domain;

namespace AnalyzeRepo.Api.Features.Chat.Domain;

public sealed class ChatMessage : Entity<Guid>
{
    public Guid     SessionId { get; private set; }
    public string   Role      { get; private set; } = string.Empty;
    public string   Content   { get; private set; } = string.Empty;
    public DateTime SentAt    { get; private set; }

    private ChatMessage() { }

    public static ChatMessage Create(Guid sessionId, string role, string content)
    {
        return new ChatMessage
        {
            Id        = Guid.NewGuid(),
            SessionId = sessionId,
            Role      = role,
            Content   = content,
            SentAt    = DateTime.UtcNow
        };
    }
}
