using AnalyzeRepo.Api.Data.Application.Exceptions;
using AnalyzeRepo.Api.Data.Infrastructure;
using AnalyzeRepo.Api.Features.Analysis.RunAnalysis;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Analysis.GetAnalysis;

public class GetAnalysisHandler(AppDbContext db)
    : IRequestHandler<GetAnalysisQuery, GetAnalysisResponse>
{
    public async Task<GetAnalysisResponse> Handle(GetAnalysisQuery req, CancellationToken ct)
    {
        var analysis = await db.Analyses
            .AsNoTracking()
            .Include(a => a.Steps)
            .FirstOrDefaultAsync(a => a.Id == req.Id, ct)
            ?? throw new NotFoundException(nameof(Domain.Analysis), req.Id);

        return new GetAnalysisResponse(
            analysis.Id,
            analysis.RepoUrl,
            analysis.Query,
            analysis.MermaidCode,
            analysis.Summary,
            analysis.CreatedAt,
            analysis.Steps
                .Select(s => new AnalysisStepDto(
                    s.Number, s.Title, s.FrontendComponent,
                    s.UserAction, s.ApiEndpoint, s.BackendMethod))
                .ToList(),
            analysis.References
                .Select(r => new CodeReferenceDto(r.File, r.Snippet))
                .ToList());
    }
}
