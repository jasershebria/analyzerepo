// namespace AnalyzeRepo.Api.Services;

// public record LlmMessage(string Role, string Content);

// public record LlmStepResult(
//     int    Number,
//     string Title,
//     string FrontendComponent,
//     string UserAction,
//     string ApiEndpoint,
//     string BackendMethod);

// public record LlmCodeReference(string File, string Snippet);

// public record LlmAnalysisResult(
//     string                    MermaidCode,
//     string                    Summary,
//     IReadOnlyList<LlmStepResult>      Steps,
//     IReadOnlyList<LlmCodeReference>   CodeReferences);

// public record LlmChatResult(string Text, bool ShouldRunAnalysis);

// public interface ILlmService
// {
//     Task<LlmAnalysisResult> AnalyzeAsync(
//         string repoUrl,
//         string fileTree,
//         string query,
//         CancellationToken ct = default);

//     Task<LlmChatResult> ChatAsync(
//         string repoUrl,
//         IReadOnlyList<LlmMessage> messages,
//         CancellationToken ct = default);
// }
