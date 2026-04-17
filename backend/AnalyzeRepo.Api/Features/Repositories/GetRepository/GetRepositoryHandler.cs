using AnalyzeRepo.Api.Data.Infrastructure;
using AnalyzeRepo.Api.Features.Repositories;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Repositories.GetRepository;

public class GetRepositoryHandler : IRequestHandler<GetRepositoryQuery, GetRepositoryResponse?>
{
    private readonly ApplicationDbContext _context;

    public GetRepositoryHandler(ApplicationDbContext context) => _context = context;

    public async Task<GetRepositoryResponse?> Handle(GetRepositoryQuery request, CancellationToken cancellationToken)
    {
        var repository = await _context.Repositories
            .Include(r => r.BranchRules)
            .Include(r => r.Auth)
            .Where(r => r.Id == request.Id && !r.IsDeleted)
            .FirstOrDefaultAsync(cancellationToken);

        if (repository == null) return null;

        return new GetRepositoryResponse
        {
            Id                  = repository.Id,
            Name                = repository.Name,
            ProviderId          = repository.ProviderId,
            WebUrl              = repository.WebUrl,
            CloneUrl            = repository.CloneUrl,
            DefaultBranch       = repository.DefaultBranch,
            ProviderRepoId      = repository.ProviderRepoId,
            ProviderWorkspaceId = repository.ProviderWorkspaceId,
            IsActive            = repository.IsActive,
            LastSeenAtUtc       = repository.LastSeenAtUtc,
            CreatedAt           = repository.CreatedAt,
            UpdatedAt           = repository.UpdatedAt,
            IsDeleted           = repository.IsDeleted,
            AuthenticationType  = repository.Auth?.AuthType,
            SecretRef           = repository.Auth?.SecretRef,
            BranchRules         = repository.BranchRules.Select(br => new BranchRuleDto
            {
                Id              = br.Id,
                Pattern         = br.Pattern,
                ScanOnPush      = br.ScanOnPush,
                IsEnabled       = br.IsEnabled
            }).ToList()
        };
    }
}
