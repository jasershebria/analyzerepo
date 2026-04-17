namespace AnalyzeRepo.Api.Common;

/// <summary>
/// Base class for entities with creation and modification audit tracking (no soft delete)
/// </summary>
/// <typeparam name="TKey">Type of the entity identifier</typeparam>
public abstract class AuditedEntity<TKey> : Entity<TKey>, ICreationAudited, IModificationAudited
    where TKey : notnull
{
    public DateTime CreatedAt { get; protected set; }
    public string? CreatedBy { get; protected set; }
    public DateTime? UpdatedAt { get; protected set; }
    public string? UpdatedBy { get; protected set; }

    protected AuditedEntity()
    {
    }

    protected AuditedEntity(TKey id) : base(id)
    {
        CreatedAt = DateTime.UtcNow;
    }
    protected void SetCreationAudit(string? createdBy = null)
    {
        CreatedAt = DateTime.UtcNow;
        CreatedBy = createdBy;
    }
    protected void SetModificationAudit(string? updatedBy = null)
    {
        UpdatedAt = DateTime.UtcNow;
        UpdatedBy = updatedBy;
    }
}
