using MediatR;

namespace AnalyzeRepo.Api.Features.Repository.GetRepository;

public record GetRepositoryQuery(Guid Id) : IRequest<GetRepositoryResponse>;

public record GetRepositoryResponse(
    Guid     Id,
    string   RepoUrl,
    string   Owner,
    string   RepoName,
    bool     IsConnected,
    DateTime CreatedAt);
