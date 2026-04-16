using AnalyzeRepo.Api.Data.Domain;

namespace AnalyzeRepo.Api.Features.Analysis.Domain;

public sealed record AnalysisCompletedEvent(
    Guid AnalysisId,
    Guid ConnectionId) : DomainEvent;
