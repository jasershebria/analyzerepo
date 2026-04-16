using MediatR;
using Microsoft.Extensions.Logging;

namespace AnalyzeRepo.Api.Data.Application.Behaviors;

public class LoggingBehavior<TRequest, TResponse>(
    ILogger<LoggingBehavior<TRequest, TResponse>> logger)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken ct)
    {
        var name = typeof(TRequest).Name;
        logger.LogInformation("Handling {RequestName}", name);
        var response = await next();
        logger.LogInformation("Handled  {RequestName}", name);
        return response;
    }
}
