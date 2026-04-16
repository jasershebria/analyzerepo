namespace AnalyzeRepo.Api.Data.Domain;

public abstract class AuditedAggregateRoot<TKey> : AggregateRoot<TKey>, ICreationAudited, IModificationAudited
    where TKey : notnull
{
    public DateTime  CreatedAt { get; protected set; }
    public string?   CreatedBy { get; protected set; }
    public DateTime? UpdatedAt { get; protected set; }
    public string?   UpdatedBy { get; protected set; }

    protected AuditedAggregateRoot() { }
    protected AuditedAggregateRoot(TKey id) : base(id) { CreatedAt = DateTime.UtcNow; }
}
