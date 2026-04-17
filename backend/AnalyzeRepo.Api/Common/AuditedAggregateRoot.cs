namespace AnalyzeRepo.Api.Common;

/// <summary>
/// Base class for aggregate roots with creation and modification audit tracking (no soft delete)
/// </summary>
/// <typeparam name="TKey">Type of the aggregate root identifier</typeparam>
public abstract class AuditedAggregateRoot<TKey> : AggregateRoot<TKey>, ICreationAudited, IModificationAudited
    where TKey : notnull
{
    // Creation audit
    public DateTime CreatedAt { get; protected set; }
    public string? CreatedBy { get; protected set; }

    // Modification audit
    public DateTime? UpdatedAt { get; protected set; }
    public string? UpdatedBy { get; protected set; }

    // Parameterless constructor for EF Core
    protected AuditedAggregateRoot()
    {
    }

    protected AuditedAggregateRoot(TKey id) : base(id)
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
}
