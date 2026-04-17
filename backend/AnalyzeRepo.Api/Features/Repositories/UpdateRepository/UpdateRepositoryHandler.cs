using AnalyzeRepo.Api.Data.Infrastructure;
using AnalyzeRepo.Api.Features.Repositories;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Repositories.UpdateRepository;

public sealed class UpdateRepositoryHandler : IRequestHandler<UpdateRepositoryCommand, UpdateRepositoryResponse>
{
    private readonly ApplicationDbContext _db;

    public UpdateRepositoryHandler(ApplicationDbContext db) => _db = db;

    public async Task<UpdateRepositoryResponse> Handle(UpdateRepositoryCommand cmd, CancellationToken ct)
    {
        var repo = await _db.Repositories
            .Include(r => r.BranchRules.Where(br => !br.IsDeleted))
            .Include(r => r.Auth)
            .FirstOrDefaultAsync(r => r.Id == cmd.Id && !r.IsDeleted, ct)
            ?? throw new KeyNotFoundException($"Repository {cmd.Id} not found.");

        repo.UpdateDetails(cmd.Name, cmd.ProviderId, cmd.WebUrl);
        repo.SetProviderMeta(
            providerRepoId:     cmd.ProviderRepoId ?? repo.ProviderRepoId ?? string.Empty,
            cloneUrl:           cmd.CloneUrl,
            defaultBranch:      cmd.DefaultBranch,
            providerWorkspaceId: repo.ProviderWorkspaceId);
        repo.SetAuth(cmd.AuthenticationType, cmd.SecretRef);

        var requestedPatterns = cmd.BranchRules
            .Select(r => r.Pattern.Trim())
            .ToHashSet(StringComparer.OrdinalIgnoreCase);

        var rulesToDelete = repo.BranchRules
            .Where(r => !requestedPatterns.Contains(r.Pattern))
            .ToList();

        foreach (var rule in rulesToDelete)
            _db.Remove(rule);

        foreach (var dto in cmd.BranchRules)
        {
            var pattern  = dto.Pattern.Trim();
            var existing = repo.BranchRules.FirstOrDefault(
                r => r.Pattern.Equals(pattern, StringComparison.OrdinalIgnoreCase));

            if (existing != null)
            {
                existing.SetPattern(pattern);
                existing.SetDefaultScanMode(dto.Mode);
                existing.SetScanOnPush(dto.ScanOnPush);
                existing.SetEnabled(true);
            }
            else
            {
                repo.AddBranchRule(pattern, dto.Mode, dto.ScanOnPush);
            }
        }

        await _db.SaveChangesAsync(ct);

        return new UpdateRepositoryResponse
        {
            Id         = repo.Id,
            Name       = repo.Name,
            ProviderId = repo.ProviderId,
            WebUrl     = repo.WebUrl,
            UpdatedAt  = repo.UpdatedAt ?? DateTime.UtcNow
        };
    }
}
