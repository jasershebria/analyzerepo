using AnalyzeRepo.Api.Features.Repositories.Domain;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace AnalyzeRepo.Api.Data.Configurations;

public class BranchTrackingRuleConfiguration : IEntityTypeConfiguration<BranchTrackingRule>
{
    public void Configure(EntityTypeBuilder<BranchTrackingRule> builder)
    {
        builder.ToTable("BranchTrackingRules");
        builder.HasKey(br => br.Id);
        builder.Property(br => br.Id).ValueGeneratedNever();

        builder.Property(br => br.RepositoryId).IsRequired();
        builder.Property(br => br.Pattern).IsRequired().HasMaxLength(200);
        builder.Property(br => br.IsEnabled).IsRequired().HasDefaultValue(true);
        builder.Property(br => br.ScanOnPush).IsRequired().HasDefaultValue(true);
        builder.Property(br => br.ScanOnSchedule).IsRequired().HasDefaultValue(false);
        builder.Property(br => br.DefaultScanMode).IsRequired().HasConversion<int>().HasDefaultValue(ScanMode.Full);
        builder.Property(br => br.CreatedAt).IsRequired();
        builder.Property(br => br.UpdatedAt);
        builder.Property(br => br.DeletedAt);
        builder.Property(br => br.IsDeleted).IsRequired().HasDefaultValue(false);

        builder.HasIndex(br => new { br.RepositoryId, br.Pattern })
               .IsUnique()
               .HasFilter("\"DeletedAt\" IS NULL");

        builder.HasOne<Repository>()
               .WithMany(r => r.BranchRules)
               .HasForeignKey(br => br.RepositoryId)
               .OnDelete(DeleteBehavior.Cascade);
    }
}
