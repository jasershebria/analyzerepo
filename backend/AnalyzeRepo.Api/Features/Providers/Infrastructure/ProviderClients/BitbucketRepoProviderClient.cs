using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace AnalyzeRepo.Api.Features.Providers.Infrastructure.ProviderClients;


public class BitbucketRepoProviderClient : IRepoProviderClient
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<BitbucketRepoProviderClient> _logger;
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    private const string DefaultBaseUrl = "https://api.bitbucket.org/2.0/";

    public BitbucketRepoProviderClient(HttpClient httpClient, ILogger<BitbucketRepoProviderClient> logger)
    {
        _httpClient = httpClient;
        _logger = logger;

        _httpClient.DefaultRequestHeaders.Accept.Add(
            new MediaTypeWithQualityHeaderValue("application/json"));
        _httpClient.DefaultRequestHeaders.UserAgent.Add(
            new ProductInfoHeaderValue("BitBastet", "1.0"));
    }

    public void Configure(string? apiBaseUrl)
    {
        var url = string.IsNullOrWhiteSpace(apiBaseUrl) ? DefaultBaseUrl : apiBaseUrl.TrimEnd('/') + "/";
        _httpClient.BaseAddress = new Uri(url);
    }

    public async Task<RepoMeta> GetRepoMetaAsync(
        string webUrl,
        ProviderAuth auth,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var (workspace, repoSlug) = ParseBitbucketUrl(webUrl);

            _logger.LogInformation("Fetching Bitbucket repository metadata for {Workspace}/{RepoSlug}", workspace, repoSlug);

            SetAuthHeader(auth);

            var response = await _httpClient.GetAsync($"repositories/{workspace}/{repoSlug}", cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                var errorContent = await response.Content.ReadAsStringAsync(cancellationToken);
                _logger.LogError("Bitbucket API error: {StatusCode} - {Error}", response.StatusCode, errorContent);
                throw new HttpRequestException($"Bitbucket API returned {response.StatusCode}: {errorContent}");
            }

            var content = await response.Content.ReadAsStringAsync(cancellationToken);
            var repoData = JsonSerializer.Deserialize<BitbucketRepository>(content, JsonOptions);

            if (repoData == null)
                throw new InvalidOperationException("Failed to deserialize Bitbucket repository response");

            var cloneUrl = repoData.Links?.Clone?.FirstOrDefault(l => l.Name == "https")?.Href
                ?? repoData.Links?.Clone?.FirstOrDefault()?.Href
                ?? string.Empty;

            var normalizedUrl = $"https://bitbucket.org/{workspace}/{repoSlug}";

            return new RepoMeta(
                Name: $"{workspace}/{repoSlug}",
                WebUrlNormalized: normalizedUrl,
                CloneUrl: cloneUrl,
                DefaultBranch: repoData.Mainbranch?.Name ?? "main",
                ProviderRepoId: repoData.Uuid ?? repoData.FullName,
                ProviderWorkspaceId: repoData.Workspace?.Uuid ?? repoData.Owner?.Uuid,
                ProviderCode: "bitbucket"
            );
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get repository metadata from Bitbucket");
            throw;
        }
    }

    //public async Task<bool> ValidateAuthAsync(
    //    RepoMeta meta,
    //    ProviderAuth auth,
    //    CancellationToken cancellationToken = default)
    //{
    //    try
    //    {
    //        var (workspace, repoSlug) = ParseRepoName(meta.Name);

    //        _logger.LogInformation(
    //            "Validating authentication and permissions for {Workspace}/{RepoSlug}",
    //            workspace,
    //            repoSlug);

    //        SetAuthHeader(auth);

    //        // Check effective permission on the repository
    //        var response = await _httpClient.GetAsync(
    //            $"user/permissions/repositories?q=repository.full_name=\"{workspace}/{repoSlug}\"",
    //            cancellationToken);

    //        if (!response.IsSuccessStatusCode)
    //        {
    //            _logger.LogWarning("Authentication validation failed: {StatusCode}", response.StatusCode);
    //            return false;
    //        }

    //        var content = await response.Content.ReadAsStringAsync(cancellationToken);
    //        var permissionsPage = JsonSerializer.Deserialize<BitbucketPage<BitbucketRepoPermission>>(content, JsonOptions);

    //        var permission = permissionsPage?.Values?.FirstOrDefault();

    //        if (permission == null)
    //        {
    //            _logger.LogWarning("No repository permission entry found for {Workspace}/{RepoSlug}", workspace, repoSlug);
    //            return false;
    //        }

    //        // Require admin permission
    //        if (!string.Equals(permission.Permission, "admin", StringComparison.OrdinalIgnoreCase))
    //        {
    //            _logger.LogWarning(
    //                "User does not have admin permissions for {Workspace}/{RepoSlug} (has: {Permission})",
    //                workspace, repoSlug, permission.Permission);
    //            return false;
    //        }

    //        _logger.LogInformation("Authentication validated successfully with admin permissions");
    //        return true;
    //    }
    //    catch (Exception ex)
    //    {
    //        _logger.LogError(ex, "Failed to validate authentication");
    //        return false;
    //    }
    //}

    public async Task<List<string>> GetBranchesAsync(
        RepoMeta meta,
        ProviderAuth auth,
        CancellationToken cancellationToken = default)
    {
        var (workspace, repoSlug) = ParseRepoName(meta.Name);

        SetAuthHeader(auth);

        var branches = new List<string>();
        string? nextUrl = $"repositories/{workspace}/{repoSlug}/refs/branches?pagelen=100";

        while (nextUrl != null)
        {
            var response = await _httpClient.GetAsync(nextUrl, cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                var error = await response.Content.ReadAsStringAsync(cancellationToken);
                throw new HttpRequestException($"Bitbucket API returned {response.StatusCode}: {error}");
            }

            var content = await response.Content.ReadAsStringAsync(cancellationToken);
            var page = JsonSerializer.Deserialize<BitbucketPage<BitbucketBranch>>(content, JsonOptions);

            if (page?.Values == null || page.Values.Count == 0)
                break;

            branches.AddRange(page.Values.Select(b => b.Name));

            // Bitbucket uses cursor-based pagination via the "next" field (absolute URL)
            // Strip the base address prefix so we send a relative path to the HttpClient
            nextUrl = page.Next != null
                ? MakeRelativeUrl(page.Next)
                : null;
        }

        return branches;
    }

    #region Private Helper Methods

    private void SetAuthHeader(ProviderAuth auth)
    {
        _httpClient.DefaultRequestHeaders.Authorization = null;

        switch (auth.AuthType.ToLower())
        {
            case "token":
            case "oauth":
                _httpClient.DefaultRequestHeaders.Authorization =
                    new AuthenticationHeaderValue("Bearer", auth.SecretRefOrToken);
                break;
            case "basic":
                // Expects SecretRefOrToken in "username:app_password" format
                var encoded = Convert.ToBase64String(Encoding.UTF8.GetBytes(auth.SecretRefOrToken));
                _httpClient.DefaultRequestHeaders.Authorization =
                    new AuthenticationHeaderValue("Basic", encoded);
                break;
            default:
                throw new NotSupportedException($"Auth type '{auth.AuthType}' is not supported");
        }
    }

    private static (string workspace, string repoSlug) ParseBitbucketUrl(string webUrl)
    {
        // Support formats:
        // - https://bitbucket.org/workspace/repo
        // - https://bitbucket.org/workspace/repo.git
        // - bitbucket.org/workspace/repo
        // - workspace/repo

        var normalized = webUrl.Trim()
            .Replace("https://", "")
            .Replace("http://", "")
            .Replace("bitbucket.org/", "")
            .TrimEnd('/');

        if (normalized.EndsWith(".git"))
            normalized = normalized[..^4];

        var parts = normalized.Split('/', StringSplitOptions.RemoveEmptyEntries);

        if (parts.Length < 2)
            throw new ArgumentException(
                $"Invalid Bitbucket URL format: {webUrl}. Expected format: workspace/repo",
                nameof(webUrl));

        return (parts[0], parts[1]);
    }

    private static (string workspace, string repoSlug) ParseRepoName(string name)
    {
        var parts = name.Split('/', StringSplitOptions.RemoveEmptyEntries);

        if (parts.Length != 2)
            throw new ArgumentException(
                $"Invalid repository name format: {name}. Expected format: workspace/repo",
                nameof(name));

        return (parts[0], parts[1]);
    }

    private string MakeRelativeUrl(string absoluteUrl)
    {
        var baseAddress = _httpClient.BaseAddress?.ToString().TrimEnd('/');
        if (baseAddress != null && absoluteUrl.StartsWith(baseAddress, StringComparison.OrdinalIgnoreCase))
            return absoluteUrl[baseAddress.Length..].TrimStart('/');

        // Fallback: strip scheme + host
        var uri = new Uri(absoluteUrl);
        return uri.PathAndQuery.TrimStart('/');
    }

    #endregion


    #region Bitbucket API Models

    private class BitbucketBranch
    {
        public string Name { get; set; } = default!;
    }

    private class BitbucketRepository
    {
        public string? Uuid { get; set; }
        public string FullName { get; set; } = default!;
        public BitbucketBranchRef? Mainbranch { get; set; }
        public BitbucketLinks? Links { get; set; }
        public BitbucketAccount? Owner { get; set; }
        public BitbucketAccount? Workspace { get; set; }
    }

    private class BitbucketBranchRef
    {
        public string Name { get; set; } = default!;
    }

    private class BitbucketLinks
    {
        public List<BitbucketCloneLink>? Clone { get; set; }
    }

    private class BitbucketCloneLink
    {
        public string Href { get; set; } = default!;
        public string Name { get; set; } = default!;
    }

    private class BitbucketAccount
    {
        public string? Uuid { get; set; }
        public string? DisplayName { get; set; }
    }

    private class BitbucketPage<T>
    {
        public List<T>? Values { get; set; }
        public string? Next { get; set; }
    }

    private class BitbucketRepoPermission
    {
        public string Permission { get; set; } = default!;
    }

    #endregion
}
