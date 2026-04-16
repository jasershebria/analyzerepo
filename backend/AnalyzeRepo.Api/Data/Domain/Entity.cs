namespace AnalyzeRepo.Api.Data.Domain;

public abstract class Entity<TKey> where TKey : notnull
{
    public TKey Id { get; protected set; } = default!;

    protected Entity() { }
    protected Entity(TKey id) { Id = id; }

    public override bool Equals(object? obj) =>
        obj is Entity<TKey> other &&
        GetType() == other.GetType() &&
        EqualityComparer<TKey>.Default.Equals(Id, other.Id);

    public override int GetHashCode() => HashCode.Combine(GetType(), Id);
}
