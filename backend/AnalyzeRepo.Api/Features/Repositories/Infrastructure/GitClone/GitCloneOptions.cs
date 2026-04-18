namespace AnalyzeRepo.Api.Features.Repositories.Infrastructure.GitClone;

public class GitCloneOptions
{
    public const string Section = "GitClone";

    public string BasePath { get; set; } =
        Path.Combine(Path.GetTempPath(), "analyzerepo", "repos");
}
