using AnalyzeRepo.Api.Data.Infrastructure;
using AnalyzeRepo.Api.Features.Repository.Domain;
using AnalyzeRepo.Api.Services;
using MediatR;

namespace AnalyzeRepo.Api.Features.Repository.ConnectRepository;

public class ConnectRepositoryHandler(
    AppDbContext   db,
    IGitHubService github) : IRequestHandler<ConnectRepositoryCommand, ConnectRepositoryResponse>
{
    public async Task<ConnectRepositoryResponse> Handle(
        ConnectRepositoryCommand req, CancellationToken ct)
    {
        var isReachable = await github.ValidateAccessAsync(req.RepoUrl, req.Token, ct);
        if (!isReachable)
            throw new InvalidOperationException(
                "Cannot access the repository. Check the URL and token.");

        var connection = RepoConnection.Create(req.RepoUrl, req.Token);
        db.RepoConnections.Add(connection);
        await db.SaveChangesAsync(ct);

        return new ConnectRepositoryResponse(
            connection.Id,
            connection.RepoUrl,
            connection.Owner,
            connection.RepoName,
            connection.IsConnected,
            "Repository connected successfully! I'm ready to analyze your codebase.");
    }
}
