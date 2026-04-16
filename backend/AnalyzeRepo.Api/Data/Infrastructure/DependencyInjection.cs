using AnalyzeRepo.Api.Data.Infrastructure.Interceptors;
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

        services.AddDbContext<AppDbContext>((sp, opts) =>
        {
            opts.UseNpgsql(configuration.GetConnectionString("DefaultConnection"));
            opts.AddInterceptors(
                sp.GetRequiredService<AuditInterceptor>(),
                sp.GetRequiredService<DomainEventsInterceptor>());
        });

        return services;
    }
}
