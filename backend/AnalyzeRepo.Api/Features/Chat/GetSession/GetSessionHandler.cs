using AnalyzeRepo.Api.Data.Application.Exceptions;
using AnalyzeRepo.Api.Data.Infrastructure;
using AnalyzeRepo.Api.Features.Chat.SendMessage;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Chat.GetSession;

public class GetSessionHandler(AppDbContext db)
    : IRequestHandler<GetSessionQuery, GetSessionResponse>
{
    public async Task<GetSessionResponse> Handle(GetSessionQuery req, CancellationToken ct)
    {
        var session = await db.ChatSessions
            .AsNoTracking()
            .Include(s => s.Messages.OrderBy(m => m.SentAt))
            .FirstOrDefaultAsync(s => s.Id == req.SessionId, ct)
            ?? throw new NotFoundException(nameof(Domain.ChatSession), req.SessionId);

        return new GetSessionResponse(
            session.Id,
            session.ConnectionId,
            session.RepoUrl,
            session.CreatedAt,
            session.Messages
                .Select(m => new MessageDto(m.Role, m.Content, m.SentAt))
                .ToList());
    }
}
