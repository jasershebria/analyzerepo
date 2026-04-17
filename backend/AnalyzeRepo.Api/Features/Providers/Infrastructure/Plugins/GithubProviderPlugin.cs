using AnalyzeRepo.Api.Features.Repositories.Infrastructure;
using AnalyzeRepo.Api.Features.Repositories.Webhooks;
using System.Text.Json;

namespace AnalyzeRepo.Api.Features.Providers.Infrastructure.Plugins;

/// <summary>
/// Handles GitHub "push" webhook events.
/// Payload reference: https://docs.github.com/en/webhooks/webhook-events-and-payloads#push
///
/// Parsing strategy:
///   RepositoryId  ← lookup by repository.id (GitHub integer) → internal Guid
///   Branch        ← ref, normalized: "refs/heads/main" → "main"
///   CommitHash    ← after (head commit SHA)
/// </summary>
public sealed class GithubProviderPlugin : ISourceProviderPlugin
{
    private static readonly string RefPrefix = "refs/heads/";

    private readonly IRepositoryLookupService _repositoryLookup;

    public GithubProviderPlugin(IRepositoryLookupService repositoryLookup)
    {
        _repositoryLookup = repositoryLookup;
    }


    public string ProviderCode => "github";

    public bool CanHandle(string provider) =>
        provider.Equals(ProviderCode, StringComparison.OrdinalIgnoreCase);

    public async Task<ScanJob> BuildScanJobAsync(JsonElement payload, CancellationToken ct = default)
    {
        if (!payload.TryGetProperty("repository", out var repo))
            throw new InvalidOperationException("GitHub payload is missing 'repository'.");

        if (!repo.TryGetProperty("id", out var idEl) || !idEl.TryGetInt64(out var externalId))
            throw new InvalidOperationException("GitHub payload has missing or non-integer 'repository.id'.");

        if (!payload.TryGetProperty("ref", out var refEl))
            throw new InvalidOperationException("GitHub payload is missing 'ref'.");

        var rawRef = refEl.GetString()
            ?? throw new InvalidOperationException("GitHub 'ref' is null.");

        var branch = rawRef.StartsWith(RefPrefix, StringComparison.Ordinal)
            ? rawRef[RefPrefix.Length..]
            : rawRef;

        if (!payload.TryGetProperty("after", out var afterEl))
            throw new InvalidOperationException("GitHub payload is missing 'after'.");

        var commitHash = afterEl.GetString()
            ?? throw new InvalidOperationException("GitHub 'after' is null.");

        var repositoryId = await _repositoryLookup.ResolveAsync(
            ProviderCode, externalId.ToString(), ct);

        return new ScanJob
        {
            RepositoryId = repositoryId,
            Branch       = branch,
            CommitHash   = commitHash,
            Provider     = ProviderCode
        };
    }
}
