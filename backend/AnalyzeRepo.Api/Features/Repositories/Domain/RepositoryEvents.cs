using AnalyzeRepo.Api.Common;

namespace AnalyzeRepo.Api.Features.Repositories.Domain;

public sealed class RepositoryCreatedEvent : DomainEvent
{
    public Guid   RepositoryId   { get; }
    public Guid   ProviderId     { get; }
    public string Name           { get; }
    public string WebUrl         { get; }
    public string CloneUrl       { get; private set; } = string.Empty;
    public AuthType AuthType     { get; private set; }
    public string SecretRef      { get; private set; } = string.Empty;
    public string DefaultBranch  { get; private set; } = "main";
    public bool   RunInitialScan { get; private set; }

    public List<BranchTracking> BranchRules { get; private set; } = new();

    public RepositoryCreatedEvent(
        Guid repositoryId, Guid providerId, string name, string webUrl,
        string cloneUrl, AuthType authType, string secretRef,
        string defaultBranch, bool runInitialScan, List<BranchTracking> branchRules)
    {
        RepositoryId   = repositoryId;
        ProviderId     = providerId;
        Name           = name;
        WebUrl         = webUrl;
        CloneUrl       = cloneUrl;
        AuthType       = authType;
        SecretRef      = secretRef;
        DefaultBranch  = defaultBranch;
        RunInitialScan = runInitialScan;
        BranchRules    = branchRules;
    }
}

public sealed class BranchTracking
{
    public Guid     RepositoryId    { get; set; }
    public string   Pattern         { get; set; } = string.Empty;
    public bool     IsEnabled       { get; set; } = true;
    public bool     ScanOnPush      { get; set; }
    public bool     ScanOnSchedule  { get; set; }
    public string?  Cron            { get; set; }
    public ScanMode DefaultScanMode { get; set; }
}
