using AnalyzeRepo.Api.Data.Domain;

namespace AnalyzeRepo.Api.Features.Analysis.Domain;

public sealed class AnalysisStep : Entity<Guid>
{
    public Guid   AnalysisId        { get; private set; }
    public int    Number            { get; private set; }
    public string Title             { get; private set; } = string.Empty;
    public string FrontendComponent { get; private set; } = string.Empty;
    public string UserAction        { get; private set; } = string.Empty;
    public string ApiEndpoint       { get; private set; } = string.Empty;
    public string BackendMethod     { get; private set; } = string.Empty;

    private AnalysisStep() { }

    public AnalysisStep(Guid id, Guid analysisId,
        int number, string title, string component, string userAction,
        string apiEndpoint, string backendMethod)
    {
        Id                = id;
        AnalysisId        = analysisId;
        Number            = number;
        Title             = title;
        FrontendComponent = component;
        UserAction        = userAction;
        ApiEndpoint       = apiEndpoint;
        BackendMethod     = backendMethod;
    }
}
