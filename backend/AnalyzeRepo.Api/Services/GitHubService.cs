using System.Net.Http.Headers;
using System.Text.Json;

namespace AnalyzeRepo.Api.Services;

public class GitHubService(HttpClient http) : IGitHubService
{
    private const string ApiBase = "https://api.github.com";

    public async Task<bool> ValidateAccessAsync(string repoUrl, string token, CancellationToken ct = default)
    {
        try
        {
            var (owner, repo) = ParseUrl(repoUrl);
            using var req = BuildRequest(HttpMethod.Get, $"{ApiBase}/repos/{owner}/{repo}", token);
            var resp = await http.SendAsync(req, ct);
            return resp.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public async Task<string> GetFileTreeAsync(string owner, string repo, string token, CancellationToken ct = default)
    {
        try
        {
            using var req = BuildRequest(HttpMethod.Get,
                $"{ApiBase}/repos/{owner}/{repo}/git/trees/HEAD?recursive=1", token);
            var resp = await http.SendAsync(req, ct);

            if (!resp.IsSuccessStatusCode)
                return $"(could not fetch file tree for {owner}/{repo})";

            using var stream = await resp.Content.ReadAsStreamAsync(ct);
            using var doc    = await JsonDocument.ParseAsync(stream, cancellationToken: ct);

            var paths = doc.RootElement
                .GetProperty("tree")
                .EnumerateArray()
                .Where(n => n.GetProperty("type").GetString() == "blob")
                .Select(n => n.GetProperty("path").GetString() ?? "")
                .Where(p => !string.IsNullOrEmpty(p))
                .Take(500);   // cap to avoid huge prompts

            return string.Join('\n', paths);
        }
        catch
        {
            return $"(file tree unavailable for {owner}/{repo})";
        }
    }

    private static HttpRequestMessage BuildRequest(HttpMethod method, string url, string token)
    {
        var req = new HttpRequestMessage(method, url);
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        req.Headers.UserAgent.ParseAdd("AnalyzeRepo/1.0");
        req.Headers.Accept.ParseAdd("application/vnd.github+json");
        req.Headers.Add("X-GitHub-Api-Version", "2022-11-28");
        return req;
    }

    private static (string owner, string name) ParseUrl(string url)
    {
        var parts = url.TrimEnd('/').Split('/');
        if (parts.Length < 2)
            throw new ArgumentException("Cannot parse owner/repo from URL.");
        return (parts[^2], parts[^1]);
    }
}
