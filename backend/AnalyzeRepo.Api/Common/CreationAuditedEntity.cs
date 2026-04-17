namespace AnalyzeRepo.Api.Common;

/// <summary>
/// Base class for entities with only creation audit tracking
/// Use for immutable entities that are never modified
/// </summary>
/// <typeparam name="TKey">Type of the entity identifier</typeparam>
public abstract class CreationAuditedEntity<TKey> : Entity<TKey>, ICreationAudited
    where TKey : notnull
{
    // Creation audit
    public DateTime CreatedAt { get; protected set; }
    public string? CreatedBy { get; protected set; }

    // Parameterless constructor for EF Core
    protected CreationAuditedEntity()
    {
    }

    protected CreationAuditedEntity(TKey id) : base(id)
    {
        CreatedAt = DateTime.UtcNow;
    }

    /// <summary>
    /// Sets creation audit information
    /// </summary>
    protected void SetCreationAudit(string? createdBy = null)
    {
        CreatedAt = DateTime.UtcNow;
        CreatedBy = createdBy;
    }
}
