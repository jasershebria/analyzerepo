using System.Text.RegularExpressions;
using AnalyzeRepo.Api.Common;

namespace AnalyzeRepo.Api.Features.Repositories.Domain;

public sealed class BranchTrackingRule : FullAuditedEntity<Guid>
{
    public Guid    RepositoryId   { get; private set; }
    public string  Pattern        { get; private set; } = string.Empty;
    public bool    IsEnabled      { get; private set; } = true;
    public bool    ScanOnPush     { get; private set; }
    public bool    ScanOnSchedule { get; private set; }
    public string? Cron           { get; private set; }
    public ScanMode DefaultScanMode { get; private set; }

    private BranchTrackingRule() { }

    public BranchTrackingRule(
        Guid repositoryId,
        string pattern,
        ScanMode scanMode = ScanMode.Full,
        bool scanOnPush = true)
        : base()
    {
        if (string.IsNullOrWhiteSpace(pattern))
            throw new ArgumentException("Pattern cannot be null or empty", nameof(pattern));

        Id              = Guid.NewGuid();
        RepositoryId    = repositoryId;
        Pattern         = NormalizePattern(pattern);
        DefaultScanMode = scanMode;
        ScanOnPush      = scanOnPush;
        IsEnabled       = true;
        ScanOnSchedule  = false;
        CreatedAt       = DateTime.UtcNow;
        CreatedBy       = "system";
        UpdatedAt       = DateTime.UtcNow;
    }

    public void SetPattern(string pattern)
    {
        if (string.IsNullOrWhiteSpace(pattern))
            throw new ArgumentException("Pattern cannot be null or empty", nameof(pattern));
        Pattern = NormalizePattern(pattern);
    }

    public void SetEnabled(bool enabled)
    {
        if (IsEnabled == enabled) return;
        IsEnabled = enabled;
    }

    public void SetScanOnPush(bool scanOnPush)
    {
        if (ScanOnPush == scanOnPush) return;
        ScanOnPush = scanOnPush;
    }

    public void SetDefaultScanMode(ScanMode mode)
    {
        if (DefaultScanMode == mode) return;
        DefaultScanMode = mode;
    }

    public void SetSchedule(bool enabled, string? cron)
    {
        if (enabled && string.IsNullOrWhiteSpace(cron))
            throw new ArgumentException("Cron expression is required when schedule is enabled", nameof(cron));

        ScanOnSchedule = enabled;
        Cron           = enabled ? cron?.Trim() : null;
    }

    public bool MatchesBranch(string branchName)
    {
        if (string.IsNullOrWhiteSpace(branchName)) return false;
        return BranchPatternMatcher.IsMatch(Pattern, branchName);
    }

    private static string NormalizePattern(string pattern) => pattern.Trim();
}

public enum ScanMode
{
    Full   = 1,
    Diff   = 2,
    Hybrid = 3
}

public static class BranchPatternMatcher
{
    public static bool IsMatch(string pattern, string branchName)
    {
        if (string.IsNullOrWhiteSpace(pattern) || string.IsNullOrWhiteSpace(branchName))
            return false;

        pattern    = pattern.Trim();
        branchName = branchName.Trim();

        if (pattern.Equals(branchName, StringComparison.OrdinalIgnoreCase))
            return true;

        if (pattern.Contains('*'))
        {
            var regexPattern = "^" + Regex.Escape(pattern).Replace("\\*", ".*") + "$";
            return Regex.IsMatch(branchName, regexPattern,
                RegexOptions.IgnoreCase | RegexOptions.Compiled,
                TimeSpan.FromMilliseconds(100));
        }

        return false;
    }
}
