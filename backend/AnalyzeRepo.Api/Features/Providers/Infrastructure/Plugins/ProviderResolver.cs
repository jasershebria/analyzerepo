namespace AnalyzeRepo.Api.Features.Providers.Infrastructure.Plugins;

public sealed class ProviderResolver
{
    private readonly IReadOnlyDictionary<string, ISourceProviderPlugin> _index;

    public ProviderResolver(IEnumerable<ISourceProviderPlugin> plugins)
    {
        // Key by ProviderCode for case-insensitive O(1) resolution.
        _index = plugins.ToDictionary(
            p => p.ProviderCode,
            StringComparer.OrdinalIgnoreCase);
    }

    public ISourceProviderPlugin Resolve(string provider)
    {
        if (_index.TryGetValue(provider, out var plugin))
            return plugin;

        var registered = string.Join(", ", _index.Keys);
        throw new NotSupportedException(
            $"No provider plugin registered for '{provider}'. Registered: [{registered}]");
    }
}
