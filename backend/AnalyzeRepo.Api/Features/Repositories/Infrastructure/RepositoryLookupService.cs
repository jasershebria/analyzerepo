using AnalyzeRepo.Api.Data.Infrastructure;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Repositories.Infrastructure;

public sealed class RepositoryLookupService : IRepositoryLookupService
{
    private readonly ApplicationDbContext _db;

    public RepositoryLookupService(ApplicationDbContext db) => _db = db;

    public async Task<Guid> ResolveAsync(string providerCode, string externalRepoId, CancellationToken ct = default)
    {
        var id = await _db.Repositories
            .Join(
                _db.SourceProviders,
                repo     => repo.ProviderId,
                provider => provider.Id,
                (repo, provider) => new { repo.Id, repo.ProviderRepoId, ProviderCode = provider.Code })
            .Where(x =>
                x.ProviderCode   == providerCode.ToLowerInvariant() &&
                x.ProviderRepoId == externalRepoId)
            .Select(x => (Guid?)x.Id)
            .FirstOrDefaultAsync(ct);

        if (id is null)
            throw new InvalidOperationException(
                $"No repository found for provider '{providerCode}' with external ID '{externalRepoId}'.");

        return id.Value;
    }
}
