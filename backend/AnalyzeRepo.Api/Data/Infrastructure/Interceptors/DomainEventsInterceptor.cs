using AnalyzeRepo.Api.Data.Domain;
using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Diagnostics;

namespace AnalyzeRepo.Api.Data.Infrastructure.Interceptors;

public class DomainEventsInterceptor(IMediator mediator) : SaveChangesInterceptor
{
    public override async ValueTask<int> SavedChangesAsync(
        SaveChangesCompletedEventData e,
        int result,
        CancellationToken ct = default)
    {
        if (e.Context is not null)
            await DispatchAsync(e.Context, ct);

        return await base.SavedChangesAsync(e, result, ct);
    }

    private async Task DispatchAsync(DbContext ctx, CancellationToken ct)
    {
        var entities = ctx.ChangeTracker
            .Entries<IHasDomainEvents>()
            .Where(x => x.Entity.DomainEvents.Any())
            .Select(x => x.Entity)
            .ToList();

        var events = entities.SelectMany(e => e.DomainEvents).ToList();

        foreach (var entity in entities)
            entity.ClearDomainEvents();

        foreach (var @event in events)
            await mediator.Publish(@event, ct);
    }
}
