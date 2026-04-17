using AnalyzeRepo.Api.Common;

namespace AnalyzeRepo.Api.Features.Repositories.Domain;

public sealed class RepositoryAuth : FullAuditedEntity<Guid>
{
    public Guid      RepositoryId { get; private set; }
    public AuthType  AuthType     { get; private set; }
    public string    SecretRef    { get; private set; } = string.Empty;
    public DateTime? ExpiresAt    { get; private set; }

    private RepositoryAuth() { }

    public static RepositoryAuth Create(
        Guid id, Guid repositoryId, AuthType authType, string secretRef, DateTime? expiresAt = null)
    {
        if (repositoryId == Guid.Empty)
            throw new ArgumentException("Repository ID is required", nameof(repositoryId));
        if (string.IsNullOrWhiteSpace(secretRef))
            throw new ArgumentException("Secret reference is required", nameof(secretRef));

        return new RepositoryAuth
        {
            Id           = id,
            RepositoryId = repositoryId,
            AuthType     = authType,
            SecretRef    = secretRef.Trim(),
            ExpiresAt    = expiresAt
        };
    }

    public void Update(AuthType authType, string secretRef, DateTime? expiresAt = null)
    {
        if (string.IsNullOrWhiteSpace(secretRef))
            throw new ArgumentException("Secret reference is required", nameof(secretRef));

        AuthType  = authType;
        SecretRef = secretRef.Trim();
        ExpiresAt = expiresAt;
    }

    public bool IsExpired() => ExpiresAt.HasValue && ExpiresAt.Value < DateTime.UtcNow;
}

public enum AuthType
{
    PersonalAccessToken = 1,
    OAuth               = 2,
    AppInstallation     = 3
}
