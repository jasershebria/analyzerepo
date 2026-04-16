namespace AnalyzeRepo.Api.Services;

public class LlmOptions
{
    public const string Section = "Llm";

    public string Provider { get; set; } = "OpenAI";
    public string ApiKey   { get; set; } = string.Empty;
    public string Model    { get; set; } = "gpt-4o";
    public string BaseUrl  { get; set; } = "https://api.openai.com/v1";
}
