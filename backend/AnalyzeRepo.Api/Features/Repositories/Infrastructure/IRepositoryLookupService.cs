namespace AnalyzeRepo.Api.Features.Repositories.Infrastructure;

public interface IRepositoryLookupService
{
    Task<Guid> ResolveAsync(string providerCode, string externalRepoId, CancellationToken ct = default);
}
