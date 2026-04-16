using AnalyzeRepo.Api.Data.Domain;

namespace AnalyzeRepo.Api.Features.Repository.Domain;

public sealed class RepoConnection : AuditedAggregateRoot<Guid>
{
    public string RepoUrl     { get; private set; } = string.Empty;
    public string Owner       { get; private set; } = string.Empty;
    public string RepoName    { get; private set; } = string.Empty;
    public string GitHubToken { get; private set; } = string.Empty;
    public bool   IsConnected { get; private set; }

    private RepoConnection() { }

    public static RepoConnection Create(string repoUrl, string token)
    {
        if (string.IsNullOrWhiteSpace(repoUrl))
            throw new ArgumentException("Repo URL is required.", nameof(repoUrl));
        if (string.IsNullOrWhiteSpace(token))
            throw new ArgumentException("GitHub token is required.", nameof(token));

        var (owner, name) = ParseUrl(repoUrl);

        var conn = new RepoConnection
        {
            Id          = Guid.NewGuid(),
            RepoUrl     = repoUrl.Trim(),
            Owner       = owner,
            RepoName    = name,
            GitHubToken = token.Trim(),
            IsConnected = true,
            CreatedAt   = DateTime.UtcNow
        };

        conn.AddDomainEvent(new RepoConnectedEvent(conn.Id, conn.RepoUrl));
        return conn;
    }

    public void Disconnect()
    {
        IsConnected = false;
        UpdatedAt   = DateTime.UtcNow;
    }

    private static (string owner, string name) ParseUrl(string url)
    {
        var parts = url.TrimEnd('/').Split('/');
        if (parts.Length < 2)
            throw new ArgumentException("Cannot parse owner/repo from URL.", nameof(url));
        return (parts[^2], parts[^1]);
    }
}
