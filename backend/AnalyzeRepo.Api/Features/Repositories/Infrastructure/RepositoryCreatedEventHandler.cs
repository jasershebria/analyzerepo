using AnalyzeRepo.Api.Features.Repositories.Domain;
using AnalyzeRepo.Api.Features.Repositories.Infrastructure.GitClone;
using MediatR;

namespace AnalyzeRepo.Api.Features.Repositories.Infrastructure;

public sealed class RepositoryCreatedEventHandler(
    IGitCloneService gitClone,
    ILogger<RepositoryCreatedEventHandler> logger)
    : INotificationHandler<RepositoryCreatedEvent>
{
    public async Task Handle(RepositoryCreatedEvent notification, CancellationToken ct)
    {
        if (string.IsNullOrWhiteSpace(notification.CloneUrl))
        {
            logger.LogWarning(
                "Repository {RepositoryId} has no clone URL — skipping initial clone.",
                notification.RepositoryId);
            return;
        }

        var token = notification.AuthType == AuthType.PersonalAccessToken
            ? notification.SecretRef
            : null;

        try
        {
            var localPath = await gitClone.CloneOrUpdateAsync(
                notification.CloneUrl,
                token,
                notification.DefaultBranch,
                ct);

            logger.LogInformation(
                "Repository {Name} ({RepositoryId}) cloned to {LocalPath}",
                notification.Name, notification.RepositoryId, localPath);
        }
        catch (Exception ex)
        {
            logger.LogError(ex,
                "Failed to clone repository {Name} ({RepositoryId}) from {CloneUrl}",
                notification.Name, notification.RepositoryId, notification.CloneUrl);
        }
    }
}
