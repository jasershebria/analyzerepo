using AnalyzeRepo.Api.Common;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Diagnostics;

namespace AnalyzeRepo.Api.Data.Infrastructure.Interceptors;

public class AuditInterceptor : SaveChangesInterceptor
{
    public override InterceptionResult<int> SavingChanges(
        DbContextEventData e, InterceptionResult<int> result)
    {
        Stamp(e.Context);
        return base.SavingChanges(e, result);
    }

    public override ValueTask<InterceptionResult<int>> SavingChangesAsync(
        DbContextEventData e, InterceptionResult<int> result, CancellationToken ct = default)
    {
        Stamp(e.Context);
        return base.SavingChangesAsync(e, result, ct);
    }

    private static void Stamp(DbContext? ctx)
    {
        if (ctx is null) return;
        var now = DateTime.UtcNow;

        foreach (var entry in ctx.ChangeTracker.Entries())
        {
            if (entry.State == EntityState.Added && entry.Entity is ICreationAudited)
                entry.Property(nameof(ICreationAudited.CreatedAt)).CurrentValue = now;

            if (entry.State == EntityState.Modified && entry.Entity is IModificationAudited)
                entry.Property(nameof(IModificationAudited.UpdatedAt)).CurrentValue = now;
        }
    }
}
