using AnalyzeRepo.Api.Features.Analysis.RunAnalysis;
using MediatR;

namespace AnalyzeRepo.Api.Features.Chat.SendMessage;

public record SendMessageCommand(
    Guid    ConnectionId,
    Guid?   SessionId,
    string  Message) : IRequest<SendMessageResponse>;

public record MessageDto(string Role, string Content, DateTime SentAt);

public record SendMessageResponse(
    Guid                      SessionId,
    MessageDto                UserMessage,
    MessageDto                AssistantMessage,
    RunAnalysisResponse?      AnalysisData);
