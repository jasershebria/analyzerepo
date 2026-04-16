namespace AnalyzeRepo.Api.Services;

public interface IGitHubService
{
    Task<bool>   ValidateAccessAsync(string repoUrl, string token, CancellationToken ct = default);
    Task<string> GetFileTreeAsync(string owner, string repo, string token, CancellationToken ct = default);
}
