using System.Reflection;
using Microsoft.Extensions.DependencyInjection;

namespace AnalyzeRepo.Api.Features.Providers.Infrastructure.Plugins;

public static class ProviderPluginRegistration
{
    public static IServiceCollection AddProviderPlugins(this IServiceCollection services)
    {
        var pluginInterface = typeof(ISourceProviderPlugin);

        var pluginTypes = Assembly.GetExecutingAssembly()
            .GetTypes()
            .Where(t => t is { IsClass: true, IsAbstract: false }
                        && pluginInterface.IsAssignableFrom(t));

        foreach (var pluginType in pluginTypes)
        {
            // Register as the interface so IEnumerable<ISourceProviderPlugin> injection works.
            services.AddScoped(pluginInterface, pluginType);
        }

        // ProviderResolver depends on IEnumerable<ISourceProviderPlugin> — registered above.
        services.AddScoped<ProviderResolver>();

        return services;
    }
}
