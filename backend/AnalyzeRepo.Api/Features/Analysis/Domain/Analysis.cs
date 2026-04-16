using AnalyzeRepo.Api.Data.Domain;

namespace AnalyzeRepo.Api.Features.Analysis.Domain;

public sealed class Analysis : AuditedAggregateRoot<Guid>
{
    public Guid   ConnectionId { get; private set; }
    public string RepoUrl      { get; private set; } = string.Empty;
    public string Query        { get; private set; } = string.Empty;
    public string MermaidCode  { get; private set; } = string.Empty;
    public string Summary      { get; private set; } = string.Empty;
    public int    FlowCount    { get; private set; }
    public int    QueryCount   { get; private set; }

    private readonly List<AnalysisStep>  _steps      = new();
    private readonly List<CodeReference> _references = new();

    public IReadOnlyList<AnalysisStep>  Steps      => _steps.AsReadOnly();
    public IReadOnlyList<CodeReference> References => _references.AsReadOnly();

    private Analysis() { }

    public static Analysis Create(Guid connectionId, string repoUrl, string query)
    {
        return new Analysis
        {
            Id           = Guid.NewGuid(),
            ConnectionId = connectionId,
            RepoUrl      = repoUrl,
            Query        = query,
            CreatedAt    = DateTime.UtcNow
        };
    }

    public void SetResult(
        string mermaidCode,
        string summary,
        IEnumerable<(int Number, string Title, string Component, string UserAction,
                     string ApiEndpoint, string BackendMethod)> steps,
        IEnumerable<(string File, string Snippet)> references)
    {
        MermaidCode = mermaidCode;
        Summary     = summary;

        _steps.Clear();
        foreach (var s in steps)
            _steps.Add(new AnalysisStep(Guid.NewGuid(), Id,
                s.Number, s.Title, s.Component, s.UserAction,
                s.ApiEndpoint, s.BackendMethod));

        _references.Clear();
        foreach (var r in references)
            _references.Add(new CodeReference(r.File, r.Snippet));

        FlowCount  = _steps.Count;
        QueryCount++;
        UpdatedAt  = DateTime.UtcNow;

        AddDomainEvent(new AnalysisCompletedEvent(Id, ConnectionId));
    }
}
