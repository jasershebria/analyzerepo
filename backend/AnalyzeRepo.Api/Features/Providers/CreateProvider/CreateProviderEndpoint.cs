using FastEndpoints;
using FluentValidation;
using MediatR;

namespace AnalyzeRepo.Api.Features.Providers.CreateProvider;

public class CreateProviderEndpoint : Endpoint<CreateProviderCommand, ProviderDto>
{
    private readonly IMediator _mediator;

    public CreateProviderEndpoint(IMediator mediator) => _mediator = mediator;

    public override void Configure()
    {
        Post("/providers");
        AllowAnonymous();
        Options(x => x.WithTags("Providers"));
        Summary(s =>
        {
            s.Summary = "Create a new provider";
            s.Response<ProviderDto>(201, "Provider created successfully");
            s.Response(400, "Validation failed");
        });
    }

    public override async Task HandleAsync(CreateProviderCommand req, CancellationToken ct)
    {
        var result = await _mediator.Send(req, ct);
        Response = result;
        HttpContext.Response.StatusCode = 201;
    }
}

public class CreateProviderValidator : Validator<CreateProviderCommand>
{
    public CreateProviderValidator()
    {
        RuleFor(x => x.Name).NotEmpty().MaximumLength(200);
        RuleFor(x => x.Code).NotEmpty().MaximumLength(50)
            .Matches("^[a-z0-9_-]+$").WithMessage("Code must be lowercase alphanumeric with hyphens or underscores.");
        RuleFor(x => x.ApiBaseUrl).NotEmpty().MaximumLength(500)
            .Must(url => Uri.TryCreate(url, UriKind.Absolute, out _)).WithMessage("ApiBaseUrl must be a valid URL.");
    }
}
