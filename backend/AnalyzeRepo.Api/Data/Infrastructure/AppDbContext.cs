using AnalyzeRepo.Api.Features.Analysis.Domain;
using AnalyzeRepo.Api.Features.Chat.Domain;
using AnalyzeRepo.Api.Features.Repository.Domain;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Data.Infrastructure;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<RepoConnection> RepoConnections { get; set; } = null!;
    public DbSet<Analysis>       Analyses        { get; set; } = null!;
    public DbSet<AnalysisStep>   AnalysisSteps   { get; set; } = null!;
    public DbSet<ChatSession>    ChatSessions    { get; set; } = null!;
    public DbSet<ChatMessage>    ChatMessages    { get; set; } = null!;
    // public DbSet<UserSettings>   UserSettings    { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder mb)
    {
        base.OnModelCreating(mb);
        mb.ApplyConfigurationsFromAssembly(typeof(AppDbContext).Assembly);

        // CodeReference is a keyless value object — store as a JSON column
        mb.Entity<Analysis>().OwnsMany(a => a.References, r => r.ToJson());
    }
}
