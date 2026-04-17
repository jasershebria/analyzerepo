using AnalyzeRepo.Api.Features.Repositories.Webhooks;
using System.Text.Json;

namespace AnalyzeRepo.Api.Features.Providers.Infrastructure.Plugins;

public interface ISourceProviderPlugin
{
    string ProviderCode { get; }
    bool CanHandle(string provider);
    Task<ScanJob> BuildScanJobAsync(JsonElement payload, CancellationToken ct = default);
}
