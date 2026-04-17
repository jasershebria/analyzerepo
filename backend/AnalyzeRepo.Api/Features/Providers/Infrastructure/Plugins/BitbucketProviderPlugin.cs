using AnalyzeRepo.Api.Features.Repositories.Webhooks;
using System.Text.Json;

namespace AnalyzeRepo.Api.Features.Providers.Infrastructure.Plugins;

/// <summary>
/// Handles Bitbucket "repo:push" webhook events.
/// Payload reference: https://support.atlassian.com/bitbucket-cloud/docs/event-payloads/#Push
///
/// Parsing strategy:
///   RepositoryId  ← lookup by repository.uuid → internal Guid
///   Branch        ← push.changes[0].new.name
///   CommitHash    ← push.changes[0].new.target.hash
/// </summary>
public sealed class BitbucketProviderPlugin : ISourceProviderPlugin
{
    //private readonly IRepositoryLookupService _repositoryLookup;

    public BitbucketProviderPlugin()
    {
        //_repositoryLookup = repositoryLookup;
    }

    public string ProviderCode => "bitbucket";

    public bool CanHandle(string provider) =>
        provider.Equals(ProviderCode, StringComparison.OrdinalIgnoreCase);

    public async Task<ScanJob> BuildScanJobAsync(JsonElement payload, CancellationToken ct = default)
    {

        if (!payload.TryGetProperty("repository", out var repo))
            throw new InvalidOperationException("Bitbucket payload is missing 'repository'.");

        if (!repo.TryGetProperty("uuid", out var uuidEl))
            throw new InvalidOperationException("Bitbucket payload is missing 'repository.uuid'.");

        var rawUuid = uuidEl.GetString()
            ?? throw new InvalidOperationException("Bitbucket 'repository.uuid' is null.");

        var externalRepoId = rawUuid.Trim('{', '}');

        if (!payload.TryGetProperty("push", out var push))
            throw new InvalidOperationException("Bitbucket payload is missing 'push'.");

        if (!push.TryGetProperty("changes", out var changes) || changes.GetArrayLength() == 0)
            throw new InvalidOperationException("Bitbucket 'push.changes' is missing or empty.");

        var firstChange = changes[0];

        if (!firstChange.TryGetProperty("new", out var newRef))
            throw new InvalidOperationException("Bitbucket 'push.changes[0].new' is missing.");

        if (!newRef.TryGetProperty("name", out var nameEl))
            throw new InvalidOperationException("Bitbucket 'push.changes[0].new.name' is missing.");

        var branch = nameEl.GetString()
            ?? throw new InvalidOperationException("Bitbucket branch name is null.");

        if (!newRef.TryGetProperty("target", out var target))
            throw new InvalidOperationException("Bitbucket 'push.changes[0].new.target' is missing.");

        if (!target.TryGetProperty("hash", out var hashEl))
            throw new InvalidOperationException("Bitbucket 'push.changes[0].new.target.hash' is missing.");

        var commitHash = hashEl.GetString()
            ?? throw new InvalidOperationException("Bitbucket commit hash is null.");

        //var repositoryId = await _repositoryLookup.ResolveAsync(
        //    ProviderCode, externalRepoId, ct);

        return new ScanJob
        {
            RepositoryId = new Guid(),
            Branch       = branch,
            CommitHash   = commitHash,
            Provider     = ProviderCode
        };
    }
}
