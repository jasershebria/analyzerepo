using MediatR;

namespace AnalyzeRepo.Api.Features.Repositories.TestConnection;

public record TestConnectionCommand(
    Guid    ProviderId,
    string  WebUrl,
    string  AuthType,
    string  SecretRefOrToken,
    string? OptionalClonePreference
) : IRequest<TestConnectionResponse>;

public record TestConnectionResponse(
    bool               Success,
    string?            RepoName,
    string?            ProviderRepoId,
    string?            ProviderWorkspaceId,
    string?            DefaultBranch,
    string?            CloneUrl,
    string?            WebUrlNormalized,
    string?            ErrorMessage,
    List<GitHubBranch> Branches
);

public class GitHubBranch
{
    public string Name { get; set; } = default!;
}
