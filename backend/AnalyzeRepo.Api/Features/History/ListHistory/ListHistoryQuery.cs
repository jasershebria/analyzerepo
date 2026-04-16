using MediatR;

namespace AnalyzeRepo.Api.Features.History.ListHistory;

public record ListHistoryQuery(
    string? Search = null,
    int     Page   = 1,
    int     Size   = 20) : IRequest<ListHistoryResponse>;

public record HistoryItemDto(
    Guid     Id,
    string   Name,
    string   RepoUrl,
    DateTime CreatedAt,
    int      FlowCount,
    int      QueryCount);

public record ListHistoryResponse(
    IReadOnlyList<HistoryItemDto> Items,
    int TotalCount,
    int Page,
    int Size);
