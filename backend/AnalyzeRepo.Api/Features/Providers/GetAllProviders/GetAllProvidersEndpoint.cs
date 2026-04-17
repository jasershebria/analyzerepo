using AnalyzeRepo.Api.Common;
using FastEndpoints;
using MediatR;

namespace AnalyzeRepo.Api.Features.Providers.GetAllProviders;

public class GetAllProvidersEndpoint : Endpoint<GetAllProvidersQuery, PagedResult<ProviderDto>>
{
    private readonly IMediator _mediator;

    public GetAllProvidersEndpoint(IMediator mediator) => _mediator = mediator;

    public override void Configure()
    {
        Get("/providers");
        AllowAnonymous();
        Options(x => x.WithTags("Providers"));
        Summary(s =>
        {
            s.Summary = "Get all providers";
            s.Description = "Retrieves a paginated list of source providers";
            s.Response<PagedResult<ProviderDto>>(200, "Providers retrieved successfully");
        });
    }

    public override async Task HandleAsync(GetAllProvidersQuery req, CancellationToken ct)
    {
        var result = await _mediator.Send(req, ct);
        Response = result;
    }
}
