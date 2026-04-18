using System.Diagnostics;
using Microsoft.Extensions.Options;

namespace AnalyzeRepo.Api.Features.Repositories.Infrastructure.GitClone;

public class GitCloneService(IOptions<GitCloneOptions> options, ILogger<GitCloneService> logger)
    : IGitCloneService
{
    private readonly GitCloneOptions _opts = options.Value;

    public async Task<string> CloneOrUpdateAsync(
        string repoUrl,
        string? token = null,
        string? branch = null,
        CancellationToken ct = default)
    {
        var localPath = DeriveLocalPath(repoUrl);

        if (Directory.Exists(Path.Combine(localPath, ".git")))
        {
            logger.LogInformation("Updating existing clone at {Path}", localPath);
            await RunGitAsync(localPath, ["fetch", "--prune"], ct);

            var target = branch ?? await GetDefaultBranchAsync(localPath, ct);
            await RunGitAsync(localPath, ["reset", "--hard", $"origin/{target}"], ct);
        }
        else
        {
            logger.LogInformation("Cloning {Url} into {Path}", repoUrl, localPath);
            Directory.CreateDirectory(localPath);

            var authUrl = BuildAuthUrl(repoUrl, token);
            string[] args = branch is null
                ? ["clone", authUrl, localPath]
                : ["clone", "--branch", branch, "--single-branch", authUrl, localPath];

            // Clone into parent dir so git can create the target folder
            await RunGitAsync(Directory.GetParent(localPath)!.FullName, args, ct);
        }

        return localPath;
    }

    private string DeriveLocalPath(string repoUrl)
    {
        // https://github.com/owner/repo(.git) → {BasePath}/github.com/owner/repo
        var uri = new Uri(repoUrl.TrimEnd('/'));
        var segments = uri.AbsolutePath.Trim('/').TrimEnd('/');
        if (segments.EndsWith(".git", StringComparison.OrdinalIgnoreCase))
            segments = segments[..^4];

        return Path.Combine(_opts.BasePath, uri.Host, segments.Replace('/', Path.DirectorySeparatorChar));
    }

    private static string BuildAuthUrl(string repoUrl, string? token)
    {
        if (string.IsNullOrWhiteSpace(token))
            return repoUrl;

        var uri = new Uri(repoUrl);
        return $"{uri.Scheme}://{token}@{uri.Host}{uri.PathAndQuery}";
    }

    private static async Task<string> GetDefaultBranchAsync(string repoPath, CancellationToken ct)
    {
        var result = await RunGitCaptureAsync(repoPath, ["symbolic-ref", "refs/remotes/origin/HEAD"], ct);
        // refs/remotes/origin/main → main
        return result.Trim().Split('/').Last();
    }

    private async Task RunGitAsync(string workDir, string[] args, CancellationToken ct)
    {
        var (exitCode, _, stderr) = await ExecuteAsync(workDir, args, ct);
        if (exitCode != 0)
            throw new InvalidOperationException(
                $"git {string.Join(' ', args)} failed (exit {exitCode}): {stderr}");
    }

    private static async Task<string> RunGitCaptureAsync(
        string workDir, string[] args, CancellationToken ct)
    {
        var (_, stdout, _) = await ExecuteAsync(workDir, args, ct);
        return stdout;
    }

    private static async Task<(int ExitCode, string Stdout, string Stderr)> ExecuteAsync(
        string workDir, string[] args, CancellationToken ct)
    {
        var psi = new ProcessStartInfo("git")
        {
            WorkingDirectory        = workDir,
            RedirectStandardOutput  = true,
            RedirectStandardError   = true,
            UseShellExecute         = false,
            CreateNoWindow          = true,
        };

        foreach (var arg in args)
            psi.ArgumentList.Add(arg);

        using var process = Process.Start(psi)
            ?? throw new InvalidOperationException("Failed to start git process.");

        var stdout = await process.StandardOutput.ReadToEndAsync(ct);
        var stderr = await process.StandardError.ReadToEndAsync(ct);
        await process.WaitForExitAsync(ct);

        return (process.ExitCode, stdout, stderr);
    }
}
