namespace AnalyzeRepo.Api.Common;

/// <summary>
/// Base class for aggregate roots with full audit tracking (creation, modification, and soft delete)
/// </summary>
/// <typeparam name="TKey">Type of the aggregate root identifier</typeparam>
public abstract class FullAuditedAggregateRoot<TKey> : AggregateRoot<TKey>, IFullAudited
    where TKey : notnull
{
    // Creation audit
    public DateTime CreatedAt { get; protected set; }
    public string? CreatedBy { get; protected set; }

    // Modification audit
    public DateTime? UpdatedAt { get; protected set; }
    public string? UpdatedBy { get; protected set; }

    // Soft delete audit
    public bool IsDeleted { get; protected set; }
    public DateTime? DeletedAt { get; protected set; }
    public string? DeletedBy { get; protected set; }

    // Parameterless constructor for EF Core
    protected FullAuditedAggregateRoot()
    {
    }

    protected FullAuditedAggregateRoot(TKey id) : base(id)
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

    /// <summary>
    /// Sets modification audit information
    /// </summary>
    protected void SetModificationAudit(string? updatedBy = null)
    {
        UpdatedAt = DateTime.UtcNow;
        UpdatedBy = updatedBy;
    }

    /// <summary>
    /// Marks the entity as deleted (soft delete)
    /// </summary>
    public virtual void Delete(string? deletedBy = null)
    {
        if (IsDeleted)
            return;

        IsDeleted = true;
        DeletedAt = DateTime.UtcNow;
        DeletedBy = deletedBy;
    }

    /// <summary>
    /// Restores a soft-deleted entity
    /// </summary>
    public virtual void Restore()
    {
        if (!IsDeleted)
            return;

        IsDeleted = false;
        DeletedAt = null;
        DeletedBy = null;
    }
}
