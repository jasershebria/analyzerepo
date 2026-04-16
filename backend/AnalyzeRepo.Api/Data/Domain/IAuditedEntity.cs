namespace AnalyzeRepo.Api.Data.Domain;

public interface ICreationAudited
{
    DateTime CreatedAt { get; }
    string?  CreatedBy { get; }
}

public interface IModificationAudited
{
    DateTime? UpdatedAt { get; }
    string?   UpdatedBy { get; }
}
