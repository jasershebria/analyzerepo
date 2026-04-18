using Microsoft.SemanticKernel;

namespace AnalyzeRepo.Api.Features.Shared.AI;

public static class AIServiceExtensions
{
    public static IServiceCollection AddAIServices(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        var opts = configuration.GetSection(OllamaOptions.Section).Get<OllamaOptions>()
                   ?? new OllamaOptions();

        services.AddKernel()
            .AddOpenAIChatCompletion(
                modelId:  opts.Model,
                endpoint: new Uri(opts.BaseUrl + "/v1"),
                apiKey:   "ollama");

        services.AddScoped<AIChatService>();

        return services;
    }
}
