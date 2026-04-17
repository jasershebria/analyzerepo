using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Common;

public interface IPaginationFilter
{
    int PageIndex { get; set; }
    int SkipCount { get; set; }
    int MaxResultCount { get; set; }
}

//public static class PaginationExtensions
//{
//    //public static async Task<PagedResult<TOut>> ToPagedResultAsync<T, TOut>(
//    //    this IQueryable<T> query,
//    //    IPaginationFilter request,
//    //    Func<T, TOut> selector,
//    //    CancellationToken cancellationToken = default)
//    //{
//    //    var totalCount = await query.CountAsync(cancellationToken);

//    //    var skip = request.SkipCount > 0
//    //        ? request.SkipCount
//    //        : Math.Max(0, (request.PageIndex - 1) * request.MaxResultCount);

//    //    var items = await query
//    //        .Skip(skip)
//    //        .Take(request.MaxResultCount)
//    //        .ToListAsync(cancellationToken);

//    //    return new PagedResult<TOut>
//    //    {
//    //        TotalCount = totalCount,
//    //        Items = items.Select(selector).ToList()
//    //    };
//    //}



//}

public sealed class PagedResult<T>
{
    public int TotalCount { get; init; }
    public IReadOnlyList<T> Items { get; init; } = Array.Empty<T>();
}
