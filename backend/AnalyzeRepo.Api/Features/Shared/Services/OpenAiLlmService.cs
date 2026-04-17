using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Options;

namespace AnalyzeRepo.Api.Services;

public class OpenAiLlmService(HttpClient http, IOptions<LlmOptions> options) : ILlmService
{
    private readonly LlmOptions _opts = options.Value;

    public async Task<LlmAnalysisResult> AnalyzeAsync(
        string repoUrl, string fileTree, string query, CancellationToken ct = default)
    {
        var systemPrompt = $$"""
            You are an expert code analyst. The user has connected the repository: {{repoUrl}}
            Repository file tree:
            {{fileTree}}

            Respond ONLY with a JSON object in this exact shape:
            {
              "summary": "<one paragraph summary>",
              "mermaidCode": "<flowchart TD ...>",
              "steps": [
                {
                  "number": 1,
                  "title": "<step title>",
                  "frontendComponent": "<Angular component>",
                  "userAction": "<what the user does>",
                  "apiEndpoint": "<HTTP METHOD /path>",
                  "backendMethod": "<ClassName.MethodName>"
                }
              ],
              "codeReferences": [
                { "file": "<path/to/file.ts>", "snippet": "<relevant code snippet>" }
              ]
            }
            """;

        var response = await CallOpenAiAsync(systemPrompt, query, ct);

        try
        {
            using var doc = JsonDocument.Parse(ExtractJson(response));
            var root = doc.RootElement;

            var steps = root.GetProperty("steps").EnumerateArray()
                .Select(s => new LlmStepResult(
                    s.GetProperty("number").GetInt32(),
                    s.GetProperty("title").GetString() ?? "",
                    s.GetProperty("frontendComponent").GetString() ?? "",
                    s.GetProperty("userAction").GetString() ?? "",
                    s.GetProperty("apiEndpoint").GetString() ?? "",
                    s.GetProperty("backendMethod").GetString() ?? ""))
                .ToList();

            var refs = root.GetProperty("codeReferences").EnumerateArray()
                .Select(r => new LlmCodeReference(
                    r.GetProperty("file").GetString() ?? "",
                    r.GetProperty("snippet").GetString() ?? ""))
                .ToList();

            return new LlmAnalysisResult(
                root.GetProperty("mermaidCode").GetString() ?? "",
                root.GetProperty("summary").GetString() ?? "",
                steps,
                refs);
        }
        catch
        {
            return new LlmAnalysisResult(
                "graph TD\n    A[Start] --> B[End]",
                response,
                Array.Empty<LlmStepResult>(),
                Array.Empty<LlmCodeReference>());
        }
    }

    public async Task<LlmChatResult> ChatAsync(
        string repoUrl, IReadOnlyList<LlmMessage> messages, CancellationToken ct = default)
    {
        var systemPrompt = $$"""
            You are an expert code analyst assistant. The user has connected the repository: {{repoUrl}}.
            Answer questions about the repository clearly and concisely.
            If the user asks to analyze a specific flow or feature, include the word ANALYZE_FLOW in your response.
            """;

        var lastMessage = messages.LastOrDefault()?.Content ?? "";
        var text = await CallOpenAiAsync(systemPrompt, lastMessage, ct);
        var shouldAnalyze = text.Contains("ANALYZE_FLOW", StringComparison.OrdinalIgnoreCase);
        var cleanText = text.Replace("ANALYZE_FLOW", "", StringComparison.OrdinalIgnoreCase).Trim();

        return new LlmChatResult(cleanText, shouldAnalyze);
    }

    private async Task<string> CallOpenAiAsync(string system, string user, CancellationToken ct)
    {
        http.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", _opts.ApiKey);

        var body = new
        {
            model    = _opts.Model,
            messages = new[]
            {
                new { role = "system", content = system },
                new { role = "user",   content = user   }
            }
        };

        var req = new HttpRequestMessage(HttpMethod.Post, $"{_opts.BaseUrl.TrimEnd('/')}/chat/completions")
        {
            Content = new StringContent(
                JsonSerializer.Serialize(body),
                Encoding.UTF8,
                "application/json")
        };

        var resp = await http.SendAsync(req, ct);
        resp.EnsureSuccessStatusCode();

        using var stream = await resp.Content.ReadAsStreamAsync(ct);
        using var doc    = await JsonDocument.ParseAsync(stream, cancellationToken: ct);

        return doc.RootElement
            .GetProperty("choices")[0]
            .GetProperty("message")
            .GetProperty("content")
            .GetString() ?? string.Empty;
    }

    private static string ExtractJson(string text)
    {
        var start = text.IndexOf('{');
        var end   = text.LastIndexOf('}');
        return start >= 0 && end > start ? text[start..(end + 1)] : text;
    }
}
