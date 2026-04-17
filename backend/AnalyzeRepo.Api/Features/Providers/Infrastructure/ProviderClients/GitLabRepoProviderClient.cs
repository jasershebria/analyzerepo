using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace AnalyzeRepo.Api.Features.Providers.Infrastructure.ProviderClients;

public class GitLabRepoProviderClient : IRepoProviderClient
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<GitLabRepoProviderClient> _logger;
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    private const string DefaultBaseUrl = "https://gitlab.com/api/v4/";

    public GitLabRepoProviderClient(HttpClient httpClient, ILogger<GitLabRepoProviderClient> logger)
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
            var (namespace_, projectSlug) = ParseGitLabUrl(webUrl);
            var encodedPath = Uri.EscapeDataString($"{namespace_}/{projectSlug}");

            _logger.LogInformation("Fetching GitLab repository metadata for {Namespace}/{Project}", namespace_, projectSlug);

            SetAuthHeader(auth);

            var response = await _httpClient.GetAsync($"projects/{encodedPath}", cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                var errorContent = await response.Content.ReadAsStringAsync(cancellationToken);
                _logger.LogError("GitLab API error: {StatusCode} - {Error}", response.StatusCode, errorContent);
                throw new HttpRequestException($"GitLab API returned {response.StatusCode}: {errorContent}");
            }

            var content = await response.Content.ReadAsStringAsync(cancellationToken);
            var repoData = JsonSerializer.Deserialize<GitLabProject>(content, JsonOptions);

            if (repoData == null)
                throw new InvalidOperationException("Failed to deserialize GitLab project response");

            var normalizedUrl = $"https://gitlab.com/{namespace_}/{projectSlug}";

            return new RepoMeta(
                Name: $"{namespace_}/{projectSlug}",
                WebUrlNormalized: normalizedUrl,
                CloneUrl: repoData.HttpUrlToRepo,
                DefaultBranch: repoData.DefaultBranch ?? "main",
                ProviderRepoId: repoData.Id.ToString(),
                ProviderWorkspaceId: repoData.Namespace?.Id.ToString(),
                ProviderCode: "gitlab"
            );
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get repository metadata from GitLab");
            throw;
        }
    }

    public async Task<List<string>> GetBranchesAsync(
        RepoMeta meta,
        ProviderAuth auth,
        CancellationToken cancellationToken = default)
    {
        var encodedPath = Uri.EscapeDataString(meta.Name);

        SetAuthHeader(auth);

        var branches = new List<string>();
        var page = 1;
        const int perPage = 100;

        while (true)
        {
            var response = await _httpClient.GetAsync(
                $"projects/{encodedPath}/repository/branches?per_page={perPage}&page={page}",
                cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                var error = await response.Content.ReadAsStringAsync(cancellationToken);
                throw new HttpRequestException($"GitLab API returned {response.StatusCode}: {error}");
            }

            var content = await response.Content.ReadAsStringAsync(cancellationToken);
            var pageBranches = JsonSerializer.Deserialize<List<GitLabBranch>>(content, JsonOptions);

            if (pageBranches == null || pageBranches.Count == 0)
                break;

            branches.AddRange(pageBranches.Select(b => b.Name));

            if (pageBranches.Count < perPage)
                break;

            page++;
        }

        return branches;
    }

    #region Private Helper Methods

    private void SetAuthHeader(ProviderAuth auth)
    {
        _httpClient.DefaultRequestHeaders.Authorization = null;
        _httpClient.DefaultRequestHeaders.Remove("PRIVATE-TOKEN");

        switch (auth.AuthType.ToLower())
        {
            case "token":
                // GitLab personal access tokens / project tokens use PRIVATE-TOKEN header
                _httpClient.DefaultRequestHeaders.Add("PRIVATE-TOKEN", auth.SecretRefOrToken);
                break;
            case "oauth":
                _httpClient.DefaultRequestHeaders.Authorization =
                    new AuthenticationHeaderValue("Bearer", auth.SecretRefOrToken);
                break;
            default:
                throw new NotSupportedException($"Auth type '{auth.AuthType}' is not supported");
        }
    }

    private static (string namespace_, string project) ParseGitLabUrl(string webUrl)
    {
        // Support formats:
        // - https://gitlab.com/namespace/project
        // - https://gitlab.com/namespace/project.git
        // - gitlab.com/namespace/project
        // - namespace/project

        var normalized = webUrl.Trim()
            .Replace("https://", "")
            .Replace("http://", "")
            .TrimEnd('/');

        if (normalized.EndsWith(".git"))
            normalized = normalized[..^4];

        // Strip "gitlab.com/" prefix if present
        var gitlabPrefix = "gitlab.com/";
        if (normalized.StartsWith(gitlabPrefix, StringComparison.OrdinalIgnoreCase))
            normalized = normalized[gitlabPrefix.Length..];

        var parts = normalized.Split('/', StringSplitOptions.RemoveEmptyEntries);

        if (parts.Length < 2)
            throw new ArgumentException(
                $"Invalid GitLab URL format: {webUrl}. Expected format: namespace/project",
                nameof(webUrl));

        // Support nested namespaces: take last segment as project, rest as namespace
        var project = parts[^1];
        var namespace_ = string.Join("/", parts[..^1]);

        return (namespace_, project);
    }

    #endregion


    #region GitLab API Models

    private class GitLabBranch
    {
        public string Name { get; set; } = default!;
    }

    private class GitLabProject
    {
        public long Id { get; set; }
        public string Name { get; set; } = default!;
        public string PathWithNamespace { get; set; } = default!;
        public string HttpUrlToRepo { get; set; } = default!;
        public string? DefaultBranch { get; set; }
        public GitLabNamespace? Namespace { get; set; }
    }

    private class GitLabNamespace
    {
        public long Id { get; set; }
        public string Name { get; set; } = default!;
        public string Path { get; set; } = default!;
    }

    #endregion
}
