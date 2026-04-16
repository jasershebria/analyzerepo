using AnalyzeRepo.Api.Features.Analysis.RunAnalysis;
using MediatR;

namespace AnalyzeRepo.Api.Features.Analysis.GetAnalysis;

public record GetAnalysisQuery(Guid Id) : IRequest<GetAnalysisResponse>;

public record GetAnalysisResponse(
    Guid                            Id,
    string                          RepoUrl,
    string                          Query,
    string                          MermaidCode,
    string                          Summary,
    DateTime                        CreatedAt,
    IReadOnlyList<AnalysisStepDto>  Steps,
    IReadOnlyList<CodeReferenceDto> CodeReferences);
