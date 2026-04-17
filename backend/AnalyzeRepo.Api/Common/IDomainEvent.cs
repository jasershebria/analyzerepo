using MediatR;

namespace AnalyzeRepo.Api.Common;

/// <summary>
/// Marker interface for domain events
/// Implements INotification to work with MediatR
/// </summary>
public interface IDomainEvent : INotification
{
    Guid EventId { get; }
    DateTime OccurredOnUtc { get; }
}
