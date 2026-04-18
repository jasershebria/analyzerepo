using AnalyzeRepo.Api.Common;
using MediatR;

namespace AnalyzeRepo.Api.Features.Providers;

public record GetAllProvidersQuery : IRequest<PagedResult<ProviderDto>>
{
    public int    PageIndex      { get; set; } = 1;
    public int    MaxResultCount { get; set; } = 50;
    public string? SearchTerm   { get; set; }
    public bool?  IsActive      { get; set; }
}

public record ProviderDto
{
    public Guid     Id         { get; set; }
    public string   Name       { get; set; } = default!;
    public string   Code       { get; set; } = default!;
    public string   ApiBaseUrl { get; set; } = default!;
    public bool     IsActive   { get; set; }
    public DateTime CreatedAt  { get; set; }
}

public record CreateProviderCommand : IRequest<ProviderDto>
{
    public string Name       { get; set; } = default!;
    public string Code       { get; set; } = default!;
    public string ApiBaseUrl { get; set; } = default!;
}

public record DeleteProviderCommand : IRequest<Unit>
{
    public Guid Id { get; set; }
}
