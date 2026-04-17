using AnalyzeRepo.Api.Common;
using AnalyzeRepo.Api.Data.Infrastructure;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Providers.GetAllProviders;

public class GetAllProvidersHandler : IRequestHandler<GetAllProvidersQuery, PagedResult<ProviderDto>>
{
    private readonly ApplicationDbContext _context;

    public GetAllProvidersHandler(ApplicationDbContext context) => _context = context;

    public async Task<PagedResult<ProviderDto>> Handle(GetAllProvidersQuery request, CancellationToken cancellationToken)
    {
        var query = _context.SourceProviders.AsNoTracking()
            .Where(x => !x.IsDeleted);

        if (request.IsActive.HasValue)
            query = query.Where(x => x.IsActive == request.IsActive.Value);

        if (!string.IsNullOrWhiteSpace(request.SearchTerm))
        {
            var term = request.SearchTerm.ToLower();
            query = query.Where(x =>
                x.Name.ToLower().Contains(term) ||
                x.Code.ToLower().Contains(term));
        }

        query = query.OrderBy(x => x.Name);

        var totalCount = await query.CountAsync(cancellationToken);

        var items = await query
            .Skip(Math.Max(0, (request.PageIndex - 1) * request.MaxResultCount))
            .Take(request.MaxResultCount)
            .Select(x => new ProviderDto
            {
                Id         = x.Id,
                Name       = x.Name,
                Code       = x.Code,
                ApiBaseUrl = x.ApiBaseUrl,
                IsActive   = x.IsActive,
            })
            .ToListAsync(cancellationToken);

        return new PagedResult<ProviderDto> { TotalCount = totalCount, Items = items };
    }
}
