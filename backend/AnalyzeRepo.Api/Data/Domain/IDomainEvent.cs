using MediatR;

namespace AnalyzeRepo.Api.Data.Domain;

public interface IDomainEvent : INotification
{
    Guid     EventId       { get; }
    DateTime OccurredOnUtc { get; }
}
