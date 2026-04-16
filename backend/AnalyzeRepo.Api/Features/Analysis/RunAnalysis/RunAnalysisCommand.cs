using MediatR;

namespace AnalyzeRepo.Api.Features.Analysis.RunAnalysis;

public record RunAnalysisCommand(
    Guid   ConnectionId,
    string Query) : IRequest<RunAnalysisResponse>;

public record AnalysisStepDto(
    int    Number,
    string Title,
    string FrontendComponent,
    string UserAction,
    string ApiEndpoint,
    string BackendMethod);

public record CodeReferenceDto(string File, string Snippet);

public record RunAnalysisResponse(
    Guid                             AnalysisId,
    string                           AssistantMessage,
    string                           MermaidCode,
    IReadOnlyList<AnalysisStepDto>   Steps,
    IReadOnlyList<CodeReferenceDto>  CodeReferences);
