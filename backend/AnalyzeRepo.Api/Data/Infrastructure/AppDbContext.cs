using AnalyzeRepo.Api.Features.Repository.Domain;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Data.Infrastructure;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<RepoConnection> RepoConnections { get; set; } = null!;
    // public DbSet<UserSettings>   UserSettings    { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder mb)
    {
        base.OnModelCreating(mb);
        mb.ApplyConfigurationsFromAssembly(typeof(AppDbContext).Assembly);
    }
}
