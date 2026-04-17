using AnalyzeRepo.Api.Features.Repositories.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace AnalyzeRepo.Api.Data.Configurations;

public class RepositoryConfiguration : IEntityTypeConfiguration<Repository>
{
    public void Configure(EntityTypeBuilder<Repository> builder)
    {
        builder.ToTable("Repositories");
        builder.HasKey(r => r.Id);

        builder.Property(r => r.Name).IsRequired().HasMaxLength(200);
        builder.Property(r => r.WebUrl).IsRequired().HasMaxLength(500);
        builder.Property(r => r.CloneUrl).HasMaxLength(500);
        builder.Property(r => r.DefaultBranch).IsRequired().HasMaxLength(100);
        builder.Property(r => r.ProviderId).IsRequired();
        builder.Property(r => r.ProviderRepoId).HasMaxLength(100);
        builder.Property(r => r.ProviderWorkspaceId).HasMaxLength(100);
        builder.Property(r => r.IsActive).IsRequired();
        builder.Property(r => r.LastSeenAtUtc);
        builder.Property(r => r.CreatedAt).IsRequired();
        builder.Property(r => r.UpdatedAt);
        builder.Property(r => r.DeletedAt);
        builder.Property(r => r.IsDeleted).IsRequired().HasDefaultValue(false);

        builder.OwnsOne(r => r.Auth, auth =>
        {
            auth.ToTable("RepositoryAuths");
            auth.WithOwner().HasForeignKey(a => a.RepositoryId);
            auth.HasKey(a => a.Id);
            auth.Property(a => a.AuthType).IsRequired().HasConversion<int>();
            auth.Property(a => a.SecretRef).IsRequired().HasMaxLength(500);
            auth.Property(a => a.ExpiresAt);
            auth.Property(a => a.CreatedAt).IsRequired();
            auth.Property(a => a.UpdatedAt);
            auth.Property(a => a.DeletedAt);
            auth.Property(a => a.IsDeleted).IsRequired().HasDefaultValue(false);
        });

        builder.Navigation(r => r.BranchRules)
               .UsePropertyAccessMode(PropertyAccessMode.Property);

        builder.Ignore(r => r.DomainEvents);
    }
}
