using AnalyzeRepo.Api.Features.Repositories.Webhooks;
using System.Text.Json;

namespace AnalyzeRepo.Api.Features.Providers.Infrastructure.Plugins;

/// <summary>
/// Handles GitLab "Push Hook" webhook events.
/// Payload reference: https://docs.gitlab.com/ee/user/project/integrations/webhook_events.html#push-events
///
/// Parsing strategy:
///   RepositoryId  ← lookup by project.id (GitLab integer) → internal Guid
///   Branch        ← ref, normalized: "refs/heads/main" → "main"
///   CommitHash    ← checkout_sha
/// </summary>
public sealed class GitlabProviderPlugin : ISourceProviderPlugin
{
    private static readonly string RefPrefix = "refs/heads/";

    //private readonly IRepositoryLookupService _repositoryLookup;

    public GitlabProviderPlugin()
    {
        //_repositoryLookup = repositoryLookup;
    }

    public string ProviderCode => "gitlab";

    public bool CanHandle(string provider) =>
        provider.Equals(ProviderCode, StringComparison.OrdinalIgnoreCase);

    public async Task<ScanJob> BuildScanJobAsync(JsonElement payload, CancellationToken ct = default)
    {
        // ── project.id ───────────────────────────────────────────────────────
        if (!payload.TryGetProperty("project", out var project))
            throw new InvalidOperationException("GitLab payload is missing 'project'.");

        if (!project.TryGetProperty("id", out var idEl) || !idEl.TryGetInt64(out var externalId))
            throw new InvalidOperationException("GitLab payload has missing or non-integer 'project.id'.");

        // ── ref → branch ─────────────────────────────────────────────────────
        if (!payload.TryGetProperty("ref", out var refEl))
            throw new InvalidOperationException("GitLab payload is missing 'ref'.");

        var rawRef = refEl.GetString()
            ?? throw new InvalidOperationException("GitLab 'ref' is null.");

        var branch = rawRef.StartsWith(RefPrefix, StringComparison.Ordinal)
            ? rawRef[RefPrefix.Length..]
            : rawRef;

        // ── checkout_sha → commit hash ────────────────────────────────────────
        if (!payload.TryGetProperty("checkout_sha", out var shaEl))
            throw new InvalidOperationException("GitLab payload is missing 'checkout_sha'.");

        var commitHash = shaEl.GetString()
            ?? throw new InvalidOperationException("GitLab 'checkout_sha' is null.");

        //var repositoryId = await _repositoryLookup.ResolveAsync(
        //    ProviderCode, externalId.ToString(), ct);

        return new ScanJob
        {
            RepositoryId = new Guid(),
            Branch       = branch,
            CommitHash   = commitHash,
            Provider     = ProviderCode
        };
    }
}
