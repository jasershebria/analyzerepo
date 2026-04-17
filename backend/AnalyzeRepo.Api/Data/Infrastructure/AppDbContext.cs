using AnalyzeRepo.Api.Features.Providers.Domain;
using AnalyzeRepo.Api.Features.Repositories.Domain;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Data.Infrastructure;

public class ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : DbContext(options)
{
    public DbSet<Repository>     Repositories    { get; set; } = null!;
    public DbSet<SourceProvider> SourceProviders { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder mb)
    {
        base.OnModelCreating(mb);
        mb.ApplyConfigurationsFromAssembly(typeof(ApplicationDbContext).Assembly);
    }
}
