using AnalyzeRepo.Api.Data.Infrastructure.Interceptors;
using AnalyzeRepo.Api.Features.Providers.Infrastructure.ProviderClients;
using AnalyzeRepo.Api.Features.Providers.Infrastructure.Plugins;
using AnalyzeRepo.Api.Features.Repositories.Infrastructure;
using AnalyzeRepo.Api.Features.Repositories.Infrastructure.GitClone;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Data.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddDataServices(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddScoped<AuditInterceptor>();
        services.AddScoped<DomainEventsInterceptor>();

        services.AddDbContext<ApplicationDbContext>((sp, opts) =>
        {
            opts.UseNpgsql(configuration.GetConnectionString("DefaultConnection"));
            opts.AddInterceptors(
                sp.GetRequiredService<AuditInterceptor>(),
                sp.GetRequiredService<DomainEventsInterceptor>());
        });

        services.AddScoped<IRepositoryLookupService, RepositoryLookupService>();

        services.Configure<GitCloneOptions>(configuration.GetSection(GitCloneOptions.Section));
        services.AddScoped<IGitCloneService, GitCloneService>();

        services.AddHttpClient<GitHubRepoProviderClient>();
        services.AddHttpClient<BitbucketRepoProviderClient>();
        services.AddHttpClient<GitLabRepoProviderClient>();

        services.AddSingleton<RepoProviderClientFactory>(sp =>
            new RepoProviderClientFactory(sp));
        services.AddSingleton<ProviderResolver>(sp =>
            new ProviderResolver(sp.GetServices<ISourceProviderPlugin>()));

        return services;
    }
}
