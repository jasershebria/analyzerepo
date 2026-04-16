namespace AnalyzeRepo.Api.Data.Domain;

public abstract class AggregateRoot<TKey> : Entity<TKey>, IHasDomainEvents
    where TKey : notnull
{
    private readonly List<IDomainEvent> _events = new();
    public IReadOnlyCollection<IDomainEvent> DomainEvents => _events.AsReadOnly();

    protected AggregateRoot() { }
    protected AggregateRoot(TKey id) : base(id) { }

    protected void AddDomainEvent(IDomainEvent e) => _events.Add(e);
    public void ClearDomainEvents()               => _events.Clear();
}
