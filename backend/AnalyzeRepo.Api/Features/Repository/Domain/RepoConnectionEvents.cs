using AnalyzeRepo.Api.Data.Domain;

namespace AnalyzeRepo.Api.Features.Repository.Domain;

public sealed record RepoConnectedEvent(
    Guid   ConnectionId,
    string RepoUrl) : DomainEvent;
