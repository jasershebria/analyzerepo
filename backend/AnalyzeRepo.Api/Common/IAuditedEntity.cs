namespace AnalyzeRepo.Api.Common;

public interface ICreationAudited
{
    DateTime CreatedAt { get; }
    string? CreatedBy { get; }
}


public interface IModificationAudited
{
    DateTime? UpdatedAt { get; }
    string? UpdatedBy { get; }
}


public interface ISoftDelete
{
    bool IsDeleted { get; }
    DateTime? DeletedAt { get; }
    string? DeletedBy { get; }
}


public interface IFullAudited : ICreationAudited, IModificationAudited, ISoftDelete
{
}
