using FastEndpoints;
using FluentValidation;
using MediatR;

namespace AnalyzeRepo.Api.Features.Repositories.TestConnection;

public class TestConnectionEndpoint : Endpoint<TestConnectionCommand, TestConnectionResponse>
{
    private readonly IMediator _mediator;

    public TestConnectionEndpoint(IMediator mediator) => _mediator = mediator;

    public override void Configure()
    {
        Post("/repositories/test-connection");
        AllowAnonymous();
        Options(x => x.WithTags("Repositories"));
        Summary(s =>
        {
            s.Summary = "Test repository connection (Step 1)";
            s.Description = "Validates connection to repository and returns metadata. Does NOT persist anything.";
            s.Response<TestConnectionResponse>(200, "Connection test result");
            s.Response(400, "Validation failed");
        });
    }

    public override async Task HandleAsync(TestConnectionCommand req, CancellationToken ct)
    {
        var result = await _mediator.Send(req, ct);
        Response = result;
    }
}

public class TestConnectionValidator : Validator<TestConnectionCommand>
{
    public TestConnectionValidator()
    {
        RuleFor(x => x.ProviderId).NotEmpty();
        RuleFor(x => x.WebUrl).NotEmpty()
            .Must(url => Uri.TryCreate(url, UriKind.Absolute, out _)).WithMessage("Web URL must be a valid URL");
        RuleFor(x => x.AuthType).NotEmpty()
            .Must(t => new[] { "token", "oauth", "app" }.Contains(t.ToLower()))
            .WithMessage("Auth type must be 'token', 'oauth', or 'app'");
        RuleFor(x => x.SecretRefOrToken).NotEmpty();
    }
}
