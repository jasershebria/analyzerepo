using AnalyzeRepo.Api.Features.Chat.SendMessage;
using MediatR;

namespace AnalyzeRepo.Api.Features.Chat.GetSession;

public record GetSessionQuery(Guid SessionId) : IRequest<GetSessionResponse>;

public record GetSessionResponse(
    Guid                         SessionId,
    Guid                         ConnectionId,
    string                       RepoUrl,
    DateTime                     CreatedAt,
    IReadOnlyList<MessageDto>    Messages);
