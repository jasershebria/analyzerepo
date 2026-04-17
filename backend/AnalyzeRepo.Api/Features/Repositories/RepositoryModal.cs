using AnalyzeRepo.Api.Features.Repositories.Domain;
using AnalyzeRepo.Api.Common;
using MediatR;

namespace AnalyzeRepo.Api.Features.Repositories;

public record CreateRepositoryCommand : IRequest<CreateRepositoryResponse>
{
    public Guid     ProviderId         { get; set; }
    public string   ProviderRepoId     { get; set; } = default!;
    public string   Name               { get; set; } = default!;
    public string   WebUrl             { get; set; } = default!;
    public string   CloneUrl           { get; set; } = default!;
    public string   DefaultBranch      { get; set; } = default!;
    public AuthType AuthenticationType { get; set; }
    public string   SecretRef          { get; set; } = default!;
    public bool     RunInitialScan     { get; set; } = false;
    public IEnumerable<BranchRule> BranchRules { get; set; } = new List<BranchRule>();
}

public record BranchRule
{
    public string   Pattern    { get; set; } = default!;
    public ScanMode Mode       { get; set; } = ScanMode.Hybrid;
    public bool     ScanOnPush { get; set; } = true;
}

public record CreateRepositoryResponse
{
    public Guid     Id         { get; set; }
    public string   Name       { get; set; } = default!;
    public Guid     ProviderId { get; set; }
    public string   WebUrl     { get; set; } = default!;
    public DateTime CreatedAt  { get; set; }
}

public record GetAllRepositoriesQuery : IPaginationFilter, IRequest<PagedResult<RepositoryDto>>
{
    public int    PageIndex      { get; set; } = 1;
    public int    SkipCount      { get; set; } = 0;
    public int    MaxResultCount { get; set; } = 10;
    public bool   IncludeDeleted { get; set; } = false;
    public string? SearchTerm   { get; set; }
    public Guid?   ProviderId   { get; set; }
    public bool?   IsActive     { get; set; }
}

public record RepositoryDto
{
    public Guid      Id              { get; set; }
    public string    Name            { get; set; } = default!;
    public Guid      ProviderId      { get; set; }
    public string    ProviderName    { get; set; } = default!;
    public string    WebUrl          { get; set; } = default!;
    public bool      IsActive        { get; set; }
    public DateTime  CreatedAt       { get; set; }
    public DateTime? LastSeenAtUtc   { get; set; }
    public int       BranchRulesCount { get; set; }
}

public record DeleteRepositoryCommand : IRequest<Unit>
{
    public Guid Id { get; set; }
}

public record UpdateRepositoryCommand : IRequest<UpdateRepositoryResponse>
{
    public Guid     Id                 { get; set; }
    public string   Name               { get; set; } = default!;
    public Guid     ProviderId         { get; set; }
    public string   WebUrl             { get; set; } = default!;
    public string   CloneUrl           { get; set; } = default!;
    public string   DefaultBranch      { get; set; } = default!;
    public string?  ProviderRepoId     { get; set; }
    public AuthType AuthenticationType { get; set; }
    public string   SecretRef          { get; set; } = default!;
    public IEnumerable<BranchRule> BranchRules { get; set; } = new List<BranchRule>();
}

public record UpdateRepositoryResponse
{
    public Guid     Id         { get; set; }
    public string   Name       { get; set; } = default!;
    public Guid     ProviderId { get; set; }
    public string   WebUrl     { get; set; } = default!;
    public DateTime UpdatedAt  { get; set; }
}

public record GetRepositoryQuery : IRequest<GetRepositoryResponse?>
{
    public Guid Id { get; set; }
}

public record GetRepositoryResponse
{
    public Guid      Id                  { get; set; }
    public string    Name                { get; set; } = default!;
    public Guid      ProviderId          { get; set; }
    public string    WebUrl              { get; set; } = default!;
    public string    CloneUrl            { get; set; } = default!;
    public string    DefaultBranch       { get; set; } = default!;
    public string?   ProviderRepoId      { get; set; }
    public string?   ProviderWorkspaceId { get; set; }
    public bool      IsActive            { get; set; }
    public DateTime? LastSeenAtUtc       { get; set; }
    public DateTime  CreatedAt           { get; set; }
    public DateTime? UpdatedAt           { get; set; }
    public bool      IsDeleted           { get; set; }
    public AuthType? AuthenticationType  { get; set; }
    public string?   SecretRef           { get; set; }
    public List<BranchRuleDto> BranchRules { get; set; } = new();
}

public record BranchRuleDto
{
    public Guid     Id              { get; set; }
    public string   Pattern         { get; set; } = default!;
    public ScanMode DefaultScanMode { get; set; }
    public bool     ScanOnPush      { get; set; }
    public bool     IsEnabled       { get; set; }
}
