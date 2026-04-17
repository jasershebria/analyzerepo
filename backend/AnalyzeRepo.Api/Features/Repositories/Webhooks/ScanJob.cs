namespace AnalyzeRepo.Api.Features.Repositories.Webhooks;

public sealed class ScanJob
{
    public Guid   RepositoryId { get; init; }
    public string Branch       { get; init; } = default!;
    public string CommitHash   { get; init; } = default!;
    public string Provider     { get; init; } = default!;
}
