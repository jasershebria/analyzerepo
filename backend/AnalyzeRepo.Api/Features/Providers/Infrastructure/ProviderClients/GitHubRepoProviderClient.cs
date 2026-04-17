using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace AnalyzeRepo.Api.Features.Providers.Infrastructure.ProviderClients;


public class GitHubRepoProviderClient : IRepoProviderClient
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<GitHubRepoProviderClient> _logger;
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    private const string DefaultBaseUrl = "https://api.github.com/";

    public GitHubRepoProviderClient(HttpClient httpClient, ILogger<GitHubRepoProviderClient> logger)
    {
        _httpClient = httpClient;
        _logger = logger;

        _httpClient.DefaultRequestHeaders.Accept.Add(
            new MediaTypeWithQualityHeaderValue("application/vnd.github+json"));
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
            // Parse owner and repo from web URL
            var (owner, repo) = ParseGitHubUrl(webUrl);

            _logger.LogInformation("Fetching GitHub repository metadata for {Owner}/{Repo}", owner, repo);

            // Set authorization header
            SetAuthHeader(auth);

            // Call GitHub API to get repository details
            var response = await _httpClient.GetAsync($"repos/{owner}/{repo}", cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                var errorContent = await response.Content.ReadAsStringAsync(cancellationToken);
                _logger.LogError("GitHub API error: {StatusCode} - {Error}", response.StatusCode, errorContent);

                throw new HttpRequestException(
                    $"GitHub API returned {response.StatusCode}: {errorContent}");
            }

            var content = await response.Content.ReadAsStringAsync(cancellationToken);
            var repoData = JsonSerializer.Deserialize<GitHubRepository>(content, JsonOptions);

            if (repoData == null)
                throw new InvalidOperationException("Failed to deserialize GitHub repository response");

            // Normalize web URL
            var normalizedUrl = $"https://github.com/{owner}/{repo}";

            return new RepoMeta(
                Name: $"{owner}/{repo}",
                WebUrlNormalized: normalizedUrl,
                CloneUrl: repoData.CloneUrl,
                DefaultBranch: repoData.DefaultBranch,
                ProviderRepoId: repoData.Id.ToString(),
                ProviderWorkspaceId: repoData.Owner.Id.ToString(),
                ProviderCode: "github"
            );
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get repository metadata from GitHub");
            throw;
        }
    }

    //public async Task<WebhookResult> CreateOrUpdateWebhookAsync(
    //    RepoMeta meta,
    //    ProviderAuth auth,
    //    string webhookEndpointUrl,
    //    string webhookSecret,
    //    CancellationToken cancellationToken = default)
    //{
    //    try
    //    {
    //        var (owner, repo) = ParseRepoName(meta.Name);

    //        _logger.LogInformation("Creating/updating webhook for {Owner}/{Repo}", owner, repo);

    //        // Set authorization header
    //        SetAuthHeader(auth);

    //        // Check if webhook already exists
    //        var existingWebhook = await FindExistingWebhookAsync(
    //            owner,
    //            repo,
    //            webhookEndpointUrl,
    //            cancellationToken);

    //        if (existingWebhook != null)
    //        {
    //            // Update existing webhook
    //            _logger.LogInformation(
    //                "Webhook already exists with ID {WebhookId}, updating...",
    //                existingWebhook.Id);

    //            return await UpdateWebhookAsync(
    //                owner,
    //                repo,
    //                existingWebhook.Id,
    //                webhookEndpointUrl,
    //                webhookSecret,
    //                cancellationToken);
    //        }

    //        // Create new webhook
    //        var webhookPayload = new
    //        {
    //            name = "web",
    //            active = true,
    //            events = new[] { "push", "pull_request", "create", "delete" },
    //            config = new
    //            {
    //                url = webhookEndpointUrl,
    //                content_type = "json",
    //                secret = webhookSecret,
    //                insecure_ssl = "0"
    //            }
    //        };

    //        var json = JsonSerializer.Serialize(webhookPayload, JsonOptions);
    //        var content = new StringContent(json, Encoding.UTF8, "application/json");

    //        var response = await _httpClient.PostAsync(
    //            $"repos/{owner}/{repo}/hooks",
    //            content,
    //            cancellationToken);

    //        if (!response.IsSuccessStatusCode)
    //        {
    //            var errorContent = await response.Content.ReadAsStringAsync(cancellationToken);
    //            _logger.LogError(
    //                "Failed to create webhook: {StatusCode} - {Error}",
    //                response.StatusCode,
    //                errorContent);

    //            return new WebhookResult(
    //                Success: false,
    //                ProviderWebhookId: null,
    //                ErrorMessage: $"GitHub API returned {response.StatusCode}: {errorContent}"
    //            );
    //        }

    //        var responseContent = await response.Content.ReadAsStringAsync(cancellationToken);
    //        var webhook = JsonSerializer.Deserialize<GitHubWebhook>(responseContent, JsonOptions);

    //        if (webhook == null)
    //        {
    //            return new WebhookResult(
    //                Success: false,
    //                ProviderWebhookId: null,
    //                ErrorMessage: "Failed to deserialize webhook response"
    //            );
    //        }

    //        _logger.LogInformation(
    //            "Webhook created successfully with ID {WebhookId}",
    //            webhook.Id);

    //        return new WebhookResult(
    //            Success: true,
    //            ProviderWebhookId: webhook.Id.ToString(),
    //            ErrorMessage: null
    //        );
    //    }
    //    catch (Exception ex)
    //    {
    //        _logger.LogError(ex, "Failed to create/update webhook");
    //        return new WebhookResult(
    //            Success: false,
    //            ProviderWebhookId: null,
    //            ErrorMessage: ex.Message
    //        );
    //    }
    //}

    //public async Task<bool> ValidateAuthAsync(
    //    RepoMeta meta,
    //    ProviderAuth auth,
    //    CancellationToken cancellationToken = default)
    //{
    //    try
    //    {
    //        var (owner, repo) = ParseRepoName(meta.Name);

    //        _logger.LogInformation(
    //            "Validating authentication and permissions for {Owner}/{Repo}",
    //            owner,
    //            repo);

    //        // Set authorization header
    //        SetAuthHeader(auth);

    //        // Check repository permissions
    //        var response = await _httpClient.GetAsync(
    //            $"repos/{owner}/{repo}",
    //            cancellationToken);

    //        if (!response.IsSuccessStatusCode)
    //        {
    //            _logger.LogWarning(
    //                "Authentication validation failed: {StatusCode}",
    //                response.StatusCode);
    //            return false;
    //        }

    //        var content = await response.Content.ReadAsStringAsync(cancellationToken);
    //        var repoData = JsonSerializer.Deserialize<GitHubRepository>(content, JsonOptions);

    //        if (repoData?.Permissions == null)
    //        {
    //            _logger.LogWarning("Unable to determine repository permissions");
    //            return false;
    //        }

    //        // Require admin permissions for webhook creation
    //        if (!repoData.Permissions.Admin)
    //        {
    //            _logger.LogWarning(
    //                "User does not have admin permissions for {Owner}/{Repo}",
    //                owner,
    //                repo);
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
        var (owner, repo) = ParseRepoName(meta.Name);

        SetAuthHeader(auth);

        var branches = new List<string>();
        var page = 1;
        const int perPage = 1000000;

        while (true)
        {
            var response = await _httpClient.GetAsync($"repos/{owner}/{repo}/branches?per_page={perPage}&page={page}", cancellationToken);

            if (response.Headers.TryGetValues("X-OAuth-Scopes", out var scopes))
                _logger.LogInformation("Token scopes: {Scopes}", string.Join(", ", scopes));

            if (response.Headers.TryGetValues("X-Accepted-OAuth-Scopes", out var required))
                _logger.LogInformation("Required scopes: {Scopes}", string.Join(", ", required));

            if (!response.IsSuccessStatusCode)
            {
                var error = await response.Content.ReadAsStringAsync(cancellationToken);
                throw new HttpRequestException($"GitHub API returned {response.StatusCode}: {error}");
            }

            var content = await response.Content.ReadAsStringAsync(cancellationToken);
            var pageBranches = JsonSerializer.Deserialize<List<GitHubBranch>>(content, JsonOptions);

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
        // Remove existing authorization header
        _httpClient.DefaultRequestHeaders.Authorization = null;

        // Set new authorization header based on auth type
        switch (auth.AuthType.ToLower())
        {
            case "token":
                _httpClient.DefaultRequestHeaders.Authorization =
                    new AuthenticationHeaderValue("Bearer", auth.SecretRefOrToken);
                break;
            case "oauth":
                _httpClient.DefaultRequestHeaders.Authorization =
                    new AuthenticationHeaderValue("Bearer", auth.SecretRefOrToken);
                break;
            case "app":
                // GitHub App authentication would require JWT generation
                // For now, treat as token
                _httpClient.DefaultRequestHeaders.Authorization =
                    new AuthenticationHeaderValue("Bearer", auth.SecretRefOrToken);
                break;
            default:
                throw new NotSupportedException($"Auth type '{auth.AuthType}' is not supported");
        }
    }

    private static (string owner, string repo) ParseGitHubUrl(string webUrl)
    {
        // Support formats:
        // - https://github.com/owner/repo
        // - https://github.com/owner/repo.git
        // - github.com/owner/repo
        // - owner/repo

        var normalized = webUrl.Trim()
            .Replace("https://", "")
            .Replace("http://", "")
            .Replace("github.com/", "")
            .TrimEnd('/');

        if (normalized.EndsWith(".git"))
            normalized = normalized[..^4];

        var parts = normalized.Split('/', StringSplitOptions.RemoveEmptyEntries);

        if (parts.Length < 2)
            throw new ArgumentException(
                $"Invalid GitHub URL format: {webUrl}. Expected format: owner/repo",
                nameof(webUrl));

        return (parts[0], parts[1]);
    }

    private static (string owner, string repo) ParseRepoName(string name)
    {
        var parts = name.Split('/', StringSplitOptions.RemoveEmptyEntries);

        if (parts.Length != 2)
            throw new ArgumentException(
                $"Invalid repository name format: {name}. Expected format: owner/repo",
                nameof(name));

        return (parts[0], parts[1]);
    }

    //private async Task<GitHubWebhook?> FindExistingWebhookAsync(
    //    string owner,
    //    string repo,
    //    string webhookUrl,
    //    CancellationToken cancellationToken)
    //{
    //    try
    //    {
    //        var response = await _httpClient.GetAsync(
    //            $"repos/{owner}/{repo}/hooks",
    //            cancellationToken);

    //        if (!response.IsSuccessStatusCode)
    //            return null;

    //        var content = await response.Content.ReadAsStringAsync(cancellationToken);
    //        var webhooks = JsonSerializer.Deserialize<List<GitHubWebhook>>(content, JsonOptions);

    //        if (webhooks == null)
    //            return null;

    //        // Find webhook with matching URL
    //        return webhooks.FirstOrDefault(w =>
    //            w.Config?.Url != null &&
    //            w.Config.Url.Equals(webhookUrl, StringComparison.OrdinalIgnoreCase));
    //    }
    //    catch (Exception ex)
    //    {
    //        _logger.LogWarning(ex, "Failed to check for existing webhooks");
    //        return null;
    //    }
    //}

    //private async Task<WebhookResult> UpdateWebhookAsync(
    //    string owner,
    //    string repo,
    //    long webhookId,
    //    string webhookEndpointUrl,
    //    string webhookSecret,
    //    CancellationToken cancellationToken)
    //{
    //    try
    //    {
    //        var webhookPayload = new
    //        {
    //            active = true,
    //            events = new[] { "push", "pull_request", "create", "delete" },
    //            config = new
    //            {
    //                url = webhookEndpointUrl,
    //                content_type = "json",
    //                secret = webhookSecret,
    //                insecure_ssl = "0"
    //            }
    //        };

    //        var json = JsonSerializer.Serialize(webhookPayload, JsonOptions);
    //        var content = new StringContent(json, Encoding.UTF8, "application/json");

    //        var response = await _httpClient.PatchAsync(
    //            $"repos/{owner}/{repo}/hooks/{webhookId}",
    //            content,
    //            cancellationToken);

    //        if (!response.IsSuccessStatusCode)
    //        {
    //            var errorContent = await response.Content.ReadAsStringAsync(cancellationToken);
    //            _logger.LogError(
    //                "Failed to update webhook: {StatusCode} - {Error}",
    //                response.StatusCode,
    //                errorContent);

    //            return new WebhookResult(
    //                Success: false,
    //                ProviderWebhookId: null,
    //                ErrorMessage: $"GitHub API returned {response.StatusCode}: {errorContent}"
    //            );
    //        }

    //        _logger.LogInformation("Webhook updated successfully with ID {WebhookId}", webhookId);

    //        return new WebhookResult(
    //            Success: true,
    //            ProviderWebhookId: webhookId.ToString(),
    //            ErrorMessage: null
    //        );
    //    }
    //    catch (Exception ex)
    //    {
    //        _logger.LogError(ex, "Failed to update webhook");
    //        return new WebhookResult(
    //            Success: false,
    //            ProviderWebhookId: null,
    //            ErrorMessage: ex.Message
    //        );
    //    }
    //}

    #endregion


    #region GitHub API Models

    private class GitHubBranch
    {
        public string Name { get; set; } = default!;
    }

    private class GitHubRepository
    {
        public long Id { get; set; }
        public string Name { get; set; } = default!;
        public string FullName { get; set; } = default!;
        public string CloneUrl { get; set; } = default!;
        public string DefaultBranch { get; set; } = default!;
        public GitHubOwner Owner { get; set; } = default!;
        public GitHubPermissions? Permissions { get; set; }
    }

    private class GitHubOwner
    {
        public long Id { get; set; }
        public string Login { get; set; } = default!;
    }

    private class GitHubPermissions
    {
        public bool Admin { get; set; }
        public bool Push { get; set; }
        public bool Pull { get; set; }
    }

    private class GitHubWebhook
    {
        public long Id { get; set; }
        public string Name { get; set; } = default!;
        public bool Active { get; set; }
        public List<string> Events { get; set; } = new();
        public GitHubWebhookConfig? Config { get; set; }
    }

    private class GitHubWebhookConfig
    {
        public string? Url { get; set; }
        public string? ContentType { get; set; }
        public string? InsecureSsl { get; set; }
    }

    #endregion
}
