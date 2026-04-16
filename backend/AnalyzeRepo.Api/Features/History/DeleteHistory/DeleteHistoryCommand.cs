using MediatR;

namespace AnalyzeRepo.Api.Features.History.DeleteHistory;

public record DeleteHistoryCommand(Guid Id) : IRequest<Unit>;
