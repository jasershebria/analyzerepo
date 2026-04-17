using AnalyzeRepo.Api.Features.Providers.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace AnalyzeRepo.Api.Features.Providers.Domain.Configurations;

public class SourceProviderConfiguration : IEntityTypeConfiguration<SourceProvider>
{
    public void Configure(EntityTypeBuilder<SourceProvider> builder)
    {
        builder.ToTable("SourceProviders");
        builder.HasKey(p => p.Id);

        builder.Property(p => p.Name).IsRequired().HasMaxLength(200);
        builder.Property(p => p.Code).IsRequired().HasMaxLength(50);
        builder.Property(p => p.ApiBaseUrl).IsRequired().HasMaxLength(500);
        builder.Property(p => p.IsActive).IsRequired();
        builder.Property(p => p.CreatedAt).IsRequired();
        builder.Property(p => p.UpdatedAt);
        builder.Property(p => p.DeletedAt);
        builder.Property(p => p.IsDeleted).IsRequired().HasDefaultValue(false);

        builder.HasIndex(p => p.Code).IsUnique();
        builder.Ignore(p => p.DomainEvents);
    }
}
