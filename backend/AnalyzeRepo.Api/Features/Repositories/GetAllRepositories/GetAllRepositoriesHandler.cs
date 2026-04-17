using AnalyzeRepo.Api.Data.Infrastructure;
using AnalyzeRepo.Api.Features.Providers.Domain;
using AnalyzeRepo.Api.Features.Repositories;
using AnalyzeRepo.Api.Common;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Repositories.GetAllRepositories;

public class GetAllRepositoriesHandler : IRequestHandler<GetAllRepositoriesQuery, PagedResult<RepositoryDto>>
{
    private readonly ApplicationDbContext _context;

    public GetAllRepositoriesHandler(ApplicationDbContext context) => _context = context;

    public async Task<PagedResult<RepositoryDto>> Handle(GetAllRepositoriesQuery request, CancellationToken cancellationToken)
    {
        var query = from repo in _context.Repositories
                    join provider in _context.SourceProviders on repo.ProviderId equals provider.Id
                    select new
                    {
                        Repository   = repo,
                        ProviderName = provider.Name
                    };

        query = query.AsNoTracking();

        if (!request.IncludeDeleted)
            query = query.Where(x => !x.Repository.IsDeleted);

        if (!string.IsNullOrWhiteSpace(request.SearchTerm))
        {
            var term = request.SearchTerm.ToLower();
            query = query.Where(x =>
                x.Repository.Name.ToLower().Contains(term) ||
                x.Repository.WebUrl.ToLower().Contains(term));
        }

        if (request.ProviderId.HasValue)
            query = query.Where(x => x.Repository.ProviderId == request.ProviderId.Value);

        if (request.IsActive.HasValue)
            query = query.Where(x => x.Repository.IsActive == request.IsActive.Value);

        query = query.OrderByDescending(x => x.Repository.CreatedAt);

        var totalCount = await query.CountAsync(cancellationToken);

        var skip = request.SkipCount > 0
            ? request.SkipCount
            : Math.Max(0, (request.PageIndex - 1) * request.MaxResultCount);

        var items = await query
            .Skip(skip)
            .Take(request.MaxResultCount)
            .Select(x => new RepositoryDto
            {
                Id               = x.Repository.Id,
                Name             = x.Repository.Name,
                ProviderId       = x.Repository.ProviderId,
                ProviderName     = x.ProviderName,
                WebUrl           = x.Repository.WebUrl,
                IsActive         = x.Repository.IsActive,
                CreatedAt        = x.Repository.CreatedAt,
                LastSeenAtUtc    = x.Repository.LastSeenAtUtc,
                BranchRulesCount = x.Repository.BranchRules.Count
            })
            .ToListAsync(cancellationToken);

        return new PagedResult<RepositoryDto> { TotalCount = totalCount, Items = items };
    }
}
