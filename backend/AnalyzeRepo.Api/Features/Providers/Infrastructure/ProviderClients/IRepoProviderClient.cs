namespace AnalyzeRepo.Api.Features.Providers.Infrastructure.ProviderClients;


public interface IRepoProviderClient
{
    Task<RepoMeta> GetRepoMetaAsync(string webUrl, ProviderAuth auth, CancellationToken cancellationToken = default);

    //Task<WebhookResult> CreateOrUpdateWebhookAsync(
    //    RepoMeta meta,
    //    ProviderAuth auth,
    //    string webhookEndpointUrl,
    //    string webhookSecret,
    //    CancellationToken cancellationToken = default);


    Task<List<string>> GetBranchesAsync(
    RepoMeta meta,
    ProviderAuth auth,
    CancellationToken cancellationToken = default);

    //Task<bool> ValidateAuthAsync(RepoMeta meta, ProviderAuth auth, CancellationToken cancellationToken = default);
}


public record RepoMeta(
    string Name,                    // e.g., "owner/repo"
    string WebUrlNormalized,        // Normalized web URL
    string CloneUrl,                // Git clone URL
    string DefaultBranch,           // e.g., "main", "master"
    string ProviderRepoId,          // Provider's internal ID
    string? ProviderWorkspaceId,    // Optional workspace/org ID
    string ProviderCode             // "github", "gitlab", "bitbucket"
);


public record ProviderAuth(
    string AuthType,                // "token", "oauth", "app"
    string SecretRefOrToken         // Secret reference or actual token (for test connection only)
);


public record WebhookResult(
    bool Success,
    string? ProviderWebhookId,
    string? ErrorMessage
);
