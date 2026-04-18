namespace AnalyzeRepo.Api.Features.Shared.AI;

public sealed class OllamaOptions
{
    public const string Section = "Ollama";
    public string BaseUrl  { get; set; } = "http://localhost:11434";
    public string Model    { get; set; } = "llama3.2";
}
