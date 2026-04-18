namespace AnalyzeRepo.Api.Features.Repositories.Infrastructure.GitClone;

public interface IGitCloneService
{
    /// <summary>
    /// Clones the repository to a local path derived from the URL.
    /// If the repo is already cloned, fetches latest and resets to origin.
    /// Returns the local directory path.
    /// </summary>
    Task<string> CloneOrUpdateAsync(
        string repoUrl,
        string? token = null,
        string? branch = null,
        CancellationToken ct = default);
}
