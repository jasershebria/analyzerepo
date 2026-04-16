using MediatR;

namespace AnalyzeRepo.Api.Features.Repository.ConnectRepository;

public record ConnectRepositoryCommand(
    string RepoUrl,
    string Token) : IRequest<ConnectRepositoryResponse>;

public record ConnectRepositoryResponse(
    Guid   Id,
    string RepoUrl,
    string Owner,
    string RepoName,
    bool   IsConnected,
    string Message);
