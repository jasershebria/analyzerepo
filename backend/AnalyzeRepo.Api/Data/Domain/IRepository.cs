namespace AnalyzeRepo.Api.Data.Domain;

public interface IRepository<TAggregate, in TKey>
    where TAggregate : AggregateRoot<TKey>
    where TKey : notnull
{
    Task<TAggregate?> FindByIdAsync(TKey id, CancellationToken ct = default);
    void Add(TAggregate aggregate);
    void Remove(TAggregate aggregate);
    Task SaveChangesAsync(CancellationToken ct = default);
}
