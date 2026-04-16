using AnalyzeRepo.Api.Data.Infrastructure;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.History.ListHistory;

public class ListHistoryHandler(AppDbContext db)
    : IRequestHandler<ListHistoryQuery, ListHistoryResponse>
{
    public async Task<ListHistoryResponse> Handle(ListHistoryQuery req, CancellationToken ct)
    {
        var query = db.Analyses.AsNoTracking();

        if (!string.IsNullOrWhiteSpace(req.Search))
        {
            var s = req.Search.ToLower();
            query = query.Where(a =>
                a.RepoUrl.ToLower().Contains(s) ||
                a.Query.ToLower().Contains(s));
        }

        var total = await query.CountAsync(ct);

        var items = await query
            .OrderByDescending(a => a.CreatedAt)
            .Skip((req.Page - 1) * req.Size)
            .Take(req.Size)
            .Select(a => new HistoryItemDto(
                a.Id,
                a.Query,
                a.RepoUrl,
                a.CreatedAt,
                a.FlowCount,
                a.QueryCount))
            .ToListAsync(ct);

        return new ListHistoryResponse(items, total, req.Page, req.Size);
    }
}
