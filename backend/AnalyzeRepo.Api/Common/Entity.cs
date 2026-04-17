namespace AnalyzeRepo.Api.Common;

public abstract class Entity<TKey> : IEquatable<Entity<TKey>>
    where TKey : notnull
{
    public TKey Id { get; protected set; } = default!;

    // Parameterless constructor for EF Core
    protected Entity()
    {
    }

    protected Entity(TKey id)
    {
        Id = id;
    }

    public override bool Equals(object? obj)
    {
        return obj is Entity<TKey> entity && Equals(entity);
    }

    public bool Equals(Entity<TKey>? other)
    {
        if (other is null)
            return false;

        if (ReferenceEquals(this, other))
            return true;

        if (GetType() != other.GetType())
            return false;

        return EqualityComparer<TKey>.Default.Equals(Id, other.Id);
    }

    public override int GetHashCode()
    {
        return HashCode.Combine(GetType(), Id);
    }

    public static bool operator ==(Entity<TKey>? left, Entity<TKey>? right)
    {
        return Equals(left, right);
    }

    public static bool operator !=(Entity<TKey>? left, Entity<TKey>? right)
    {
        return !Equals(left, right);
    }
}
