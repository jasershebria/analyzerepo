using FastEndpoints;
using FluentValidation;
using MediatR;

namespace AnalyzeRepo.Api.Features.Chat.SendMessage;

public class SendMessageEndpoint(IMediator mediator)
    : Endpoint<SendMessageCommand, SendMessageResponse>
{
    public override void Configure()
    {
        Post("/chat");
        AllowAnonymous();
        Options(x => x.WithTags("Chat"));
        Summary(s =>
        {
            s.Summary     = "Send a chat message about the connected repository";
            s.Description = "Returns an AI response, optionally with analysis data";
        });
    }

    public override async Task HandleAsync(SendMessageCommand req, CancellationToken ct)
    {
        var result = await mediator.Send(req, ct);
        await SendOkAsync(result, ct);
    }
}

public class SendMessageValidator : Validator<SendMessageCommand>
{
    public SendMessageValidator()
    {
        RuleFor(x => x.ConnectionId).NotEmpty().WithMessage("ConnectionId is required.");
        RuleFor(x => x.Message)
            .NotEmpty().WithMessage("Message is required.")
            .MaximumLength(4000).WithMessage("Message must not exceed 4000 characters.");
    }
}
