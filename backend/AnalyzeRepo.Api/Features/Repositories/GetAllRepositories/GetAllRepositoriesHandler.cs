using AnalyzeRepo.Api.Data.Infrastructure;
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
        var query = _context.Repositories.AsNoTracking();

        if (!request.IncludeDeleted)
            query = query.Where(x => !x.IsDeleted);

        if (!string.IsNullOrWhiteSpace(request.SearchTerm))
        {
            var term = request.SearchTerm.ToLower();
            query = query.Where(x =>
                x.Name.ToLower().Contains(term) ||
                x.WebUrl.ToLower().Contains(term));
        }

        if (request.ProviderId.HasValue)
            query = query.Where(x => x.ProviderId == request.ProviderId.Value);

        if (request.IsActive.HasValue)
            query = query.Where(x => x.IsActive == request.IsActive.Value);

        query = query.OrderByDescending(x => x.CreatedAt);

        var totalCount = await query.CountAsync(cancellationToken);

        var skip = request.SkipCount > 0
            ? request.SkipCount
            : Math.Max(0, (request.PageIndex - 1) * request.MaxResultCount);

        var items = await query
            .Skip(skip)
            .Take(request.MaxResultCount)
            .Select(x => new RepositoryDto
            {
                Id        = x.Id,
                Name      = x.Name,
                WebUrl    = x.WebUrl,
                CreatedAt = x.CreatedAt,
            })
            .ToListAsync(cancellationToken);

        return new PagedResult<RepositoryDto> { TotalCount = totalCount, Items = items };
    }
}
