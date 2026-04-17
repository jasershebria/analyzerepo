using AnalyzeRepo.Api.Common;

namespace AnalyzeRepo.Api.Features.Repositories.Domain;

public sealed class Repository : FullAuditedAggregateRoot<Guid>
{
    public string Name { get; private set; } = string.Empty;
    public string WebUrl { get; private set; } = string.Empty;
    public string CloneUrl { get; private set; } = string.Empty;
    public string DefaultBranch { get; private set; } = "main";
    public Guid ProviderId { get; private set; }
    public RepositoryAuth? Auth { get; private set; }
    public string? ProviderRepoId { get; private set; }
    public string? ProviderWorkspaceId { get; private set; }
    public DateTime? LastSeenAtUtc { get; private set; }
    public bool IsActive { get; private set; } = true;
    public List<BranchTrackingRule> BranchRules { get; private set; } = new();

    private Repository() { }

    public static Repository Create(
        string name,
        Guid providerId,
        string webUrl,
        string providerRepoId,
        string cloneUrl,
        string defaultBranch,
        AuthType authType,
        string secretRef,
        IEnumerable<(string Pattern, bool ScanOnPush)> branchRules,
        bool runInitialScan = false)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("Name is required.", nameof(name));
        if (providerId == Guid.Empty)
            throw new ArgumentException("ProviderId is required.", nameof(providerId));
        if (string.IsNullOrWhiteSpace(webUrl))
            throw new ArgumentException("WebUrl is required.", nameof(webUrl));

        var repo = new Repository
        {
            Id         = Guid.NewGuid(),
            Name       = name.Trim(),
            ProviderId = providerId,
            WebUrl     = webUrl.Trim(),
            IsActive   = true,
            CreatedAt  = DateTime.UtcNow,
        };

        repo.SetProviderMeta(providerRepoId, cloneUrl, defaultBranch);
        repo.SetAuth(authType, secretRef);

        foreach (var rule in branchRules)
            repo.AddBranchRule(rule.Pattern, rule.ScanOnPush);

        var branchTrackings = repo.BranchRules.Select(r => new BranchTracking
        {
            RepositoryId    = r.RepositoryId,
            Pattern         = r.Pattern,
            IsEnabled       = r.IsEnabled,
            ScanOnPush      = r.ScanOnPush
        }).ToList();

        repo.AddDomainEvent(new RepositoryCreatedEvent(
            repo.Id, repo.ProviderId, repo.Name, repo.WebUrl, repo.CloneUrl,
            repo.Auth!.AuthType, repo.Auth.SecretRef, repo.DefaultBranch,
            runInitialScan, branchTrackings));

        return repo;
    }

    public void UpdateDetails(string name, Guid providerId, string webUrl)
    {
        if (string.IsNullOrWhiteSpace(name))
            throw new ArgumentException("Name is required.", nameof(name));
        if (providerId == Guid.Empty)
            throw new ArgumentException("ProviderId is required.", nameof(providerId));
        if (string.IsNullOrWhiteSpace(webUrl))
            throw new ArgumentException("WebUrl is required.", nameof(webUrl));

        Name       = name.Trim();
        ProviderId = providerId;
        WebUrl     = webUrl.Trim();
    }

    public void SetProviderMeta(
        string providerRepoId,
        string cloneUrl,
        string? defaultBranch = null,
        string? providerWorkspaceId = null)
    {
        if (string.IsNullOrWhiteSpace(providerRepoId))
            throw new ArgumentException("ProviderRepoId is required.", nameof(providerRepoId));
        if (string.IsNullOrWhiteSpace(cloneUrl))
            throw new ArgumentException("CloneUrl is required.", nameof(cloneUrl));

        ProviderRepoId      = providerRepoId.Trim();
        CloneUrl            = cloneUrl.Trim();
        ProviderWorkspaceId = string.IsNullOrWhiteSpace(providerWorkspaceId) ? null : providerWorkspaceId.Trim();

        if (!string.IsNullOrWhiteSpace(defaultBranch))
            DefaultBranch = defaultBranch.Trim();
    }

    public void SetAuth(AuthType authType, string secretRef, DateTime? expiresAt = null)
    {
        if (string.IsNullOrWhiteSpace(secretRef))
            throw new ArgumentException("Secret reference is required.", nameof(secretRef));

        if (Auth == null)
            Auth = RepositoryAuth.Create(Guid.NewGuid(), Id, authType, secretRef, expiresAt);
        else
            Auth.Update(authType, secretRef, expiresAt);
    }

    public void SetActive(bool isActive) => IsActive = isActive;

    public void TouchSeenNow() => LastSeenAtUtc = DateTime.UtcNow;

    public BranchTrackingRule AddBranchRule(string pattern ,bool scanOnPush = true)
    {
        pattern = (pattern ?? string.Empty).Trim();
        if (string.IsNullOrWhiteSpace(pattern))
            throw new ArgumentException("Pattern is required.", nameof(pattern));

        if (BranchRules.Any(x => x.Pattern.Equals(pattern, StringComparison.OrdinalIgnoreCase)))
            throw new InvalidOperationException($"Branch rule '{pattern}' already exists.");

        var rule = new BranchTrackingRule(Id, pattern,scanOnPush);
        BranchRules.Add(rule);
        return rule;
    }

    public void UpdateBranchRule(Guid ruleId, string pattern, bool scanOnPush, bool isEnabled, bool scanOnSchedule = false, string? cron = null)
    {
        var rule = BranchRules.FirstOrDefault(x => x.Id == ruleId)
                   ?? throw new KeyNotFoundException("Branch rule not found.");

        pattern = (pattern ?? string.Empty).Trim();
        if (string.IsNullOrWhiteSpace(pattern))
            throw new ArgumentException("Pattern is required.", nameof(pattern));

        if (!rule.Pattern.Equals(pattern, StringComparison.OrdinalIgnoreCase)
            && BranchRules.Any(x => x.Pattern.Equals(pattern, StringComparison.OrdinalIgnoreCase)))
            throw new InvalidOperationException($"Branch rule '{pattern}' already exists.");

        rule.SetPattern(pattern);
        rule.SetScanOnPush(scanOnPush);
        rule.SetEnabled(isEnabled);
    }

    public void RemoveBranchRule(Guid ruleId)
    {
        var rule = BranchRules.FirstOrDefault(x => x.Id == ruleId)
                   ?? throw new KeyNotFoundException("Branch rule not found.");
        BranchRules.Remove(rule);
    }

    public bool ShouldScanOnPush(string branchName)
    {
        if (!IsActive) return false;
        branchName = (branchName ?? string.Empty).Trim();
        if (string.IsNullOrWhiteSpace(branchName)) return false;
        return BranchRules.Any(r => r.IsEnabled && r.ScanOnPush && BranchPatternMatcher.IsMatch(r.Pattern, branchName));
    }

}
