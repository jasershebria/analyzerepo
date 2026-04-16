using AnalyzeRepo.Api.Data.Application.Exceptions;
using AnalyzeRepo.Api.Data.Infrastructure;
using AnalyzeRepo.Api.Features.Analysis.RunAnalysis;
using AnalyzeRepo.Api.Features.Chat.Domain;
using AnalyzeRepo.Api.Services;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Chat.SendMessage;

public class SendMessageHandler(
    AppDbContext db,
    ILlmService  llm,
    IMediator    mediator) : IRequestHandler<SendMessageCommand, SendMessageResponse>
{
    public async Task<SendMessageResponse> Handle(SendMessageCommand req, CancellationToken ct)
    {
        var connection = await db.RepoConnections
            .AsNoTracking()
            .FirstOrDefaultAsync(r => r.Id == req.ConnectionId && r.IsConnected, ct)
            ?? throw new NotFoundException("RepoConnection", req.ConnectionId);

        ChatSession session;
        if (req.SessionId.HasValue)
        {
            session = await db.ChatSessions
                .Include(s => s.Messages)
                .FirstOrDefaultAsync(s => s.Id == req.SessionId.Value, ct)
                ?? throw new NotFoundException(nameof(ChatSession), req.SessionId.Value);
        }
        else
        {
            session = ChatSession.Create(req.ConnectionId, connection.RepoUrl);
            db.ChatSessions.Add(session);
        }

        var userMsg = session.AddUserMessage(req.Message);

        var history = session.Messages
            .Select(m => new LlmMessage(m.Role, m.Content))
            .ToList();

        var chatReply = await llm.ChatAsync(connection.RepoUrl, history, ct);
        var assistantMsg = session.AddAssistantMessage(chatReply.Text);

        await db.SaveChangesAsync(ct);

        RunAnalysisResponse? analysisData = null;
        if (chatReply.ShouldRunAnalysis)
        {
            analysisData = await mediator.Send(
                new RunAnalysisCommand(req.ConnectionId, req.Message), ct);
        }

        return new SendMessageResponse(
            session.Id,
            new MessageDto(userMsg.Role,      userMsg.Content,      userMsg.SentAt),
            new MessageDto(assistantMsg.Role, assistantMsg.Content, assistantMsg.SentAt),
            analysisData);
    }
}
