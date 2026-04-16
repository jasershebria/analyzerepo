using AnalyzeRepo.Api.Data.Application.Exceptions;
using AnalyzeRepo.Api.Data.Infrastructure;
using AnalyzeRepo.Api.Services;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Analysis.RunAnalysis;

public class RunAnalysisHandler(
    AppDbContext   db,
    ILlmService    llm,
    IGitHubService github) : IRequestHandler<RunAnalysisCommand, RunAnalysisResponse>
{
    public async Task<RunAnalysisResponse> Handle(RunAnalysisCommand req, CancellationToken ct)
    {
        var connection = await db.RepoConnections
            .FirstOrDefaultAsync(r => r.Id == req.ConnectionId && r.IsConnected, ct)
            ?? throw new NotFoundException("RepoConnection", req.ConnectionId);

        var fileTree = await github.GetFileTreeAsync(
            connection.Owner, connection.RepoName, connection.GitHubToken, ct);

        var llmResult = await llm.AnalyzeAsync(
            connection.RepoUrl, fileTree, req.Query, ct);

        var analysis = Domain.Analysis.Create(req.ConnectionId, connection.RepoUrl, req.Query);

        analysis.SetResult(
            llmResult.MermaidCode,
            llmResult.Summary,
            llmResult.Steps.Select(s =>
                (s.Number, s.Title, s.FrontendComponent, s.UserAction,
                 s.ApiEndpoint, s.BackendMethod)),
            llmResult.CodeReferences.Select(r => (r.File, r.Snippet)));

        db.Analyses.Add(analysis);
        await db.SaveChangesAsync(ct);

        return new RunAnalysisResponse(
            analysis.Id,
            llmResult.Summary,
            analysis.MermaidCode,
            analysis.Steps.Select(s => new AnalysisStepDto(
                s.Number, s.Title, s.FrontendComponent,
                s.UserAction, s.ApiEndpoint, s.BackendMethod)).ToList(),
            analysis.References.Select(r => new CodeReferenceDto(r.File, r.Snippet)).ToList());
    }
}
