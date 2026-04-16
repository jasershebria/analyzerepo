using AnalyzeRepo.Api.Data.Application.Exceptions;
using AnalyzeRepo.Api.Data.Infrastructure;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.History.DeleteHistory;

public class DeleteHistoryHandler(AppDbContext db)
    : IRequestHandler<DeleteHistoryCommand, Unit>
{
    public async Task<Unit> Handle(DeleteHistoryCommand req, CancellationToken ct)
    {
        var analysis = await db.Analyses
            .FirstOrDefaultAsync(a => a.Id == req.Id, ct)
            ?? throw new NotFoundException(nameof(Features.Analysis.Domain.Analysis), req.Id);

        db.Analyses.Remove(analysis);
        await db.SaveChangesAsync(ct);
        return Unit.Value;
    }
}
