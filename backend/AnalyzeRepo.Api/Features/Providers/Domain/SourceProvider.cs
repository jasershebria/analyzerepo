using AnalyzeRepo.Api.Common;

namespace AnalyzeRepo.Api.Features.Providers.Domain;

public sealed class SourceProvider : FullAuditedAggregateRoot<Guid>
{
    public string Name       { get; private set; } = string.Empty;
    public string Code       { get; private set; } = string.Empty;
    public string ApiBaseUrl { get; private set; } = string.Empty;
    public bool   IsActive   { get; private set; } = true;

    private SourceProvider() { }

    public static SourceProvider Create(string name, string code, string apiBaseUrl)
    {
        if (string.IsNullOrWhiteSpace(name)) throw new ArgumentException("Name is required.", nameof(name));
        if (string.IsNullOrWhiteSpace(code)) throw new ArgumentException("Code is required.", nameof(code));

        return new SourceProvider
        {
            Id         = Guid.NewGuid(),
            Name       = name.Trim(),
            Code       = code.Trim().ToLowerInvariant(),
            ApiBaseUrl = apiBaseUrl.Trim(),
            IsActive   = true,
            CreatedAt  = DateTime.UtcNow
        };
    }
}
