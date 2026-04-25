import { Body, Controller, HttpCode, HttpStatus, Param, Post } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';

@ApiTags('Webhooks')
@Controller('api/webhook')
export class WebhooksController {
  @Post('trigger/:name')
  @HttpCode(HttpStatus.ACCEPTED)
  @ApiOperation({ summary: 'Receive Git provider push webhooks' })
  trigger(@Param('name') name: string, @Body() payload: Record<string, unknown>) {
    let branch = '';
    let commit = '';

    switch (name.toLowerCase()) {
      case 'github':
        branch = String(payload.ref ?? '').replace('refs/heads/', '');
        commit = String((payload.after as string) ?? '');
        break;
      case 'gitlab':
        branch = String(payload.ref ?? '').replace('refs/heads/', '');
        commit = String((payload.after as string) ?? '');
        break;
      case 'bitbucket': {
        const changes = ((payload.push as any)?.changes ?? []) as any[];
        branch = changes[0]?.new?.name ?? '';
        commit = changes[0]?.new?.target?.hash ?? '';
        break;
      }
      default:
        return { accepted: false, provider: name, error: 'Unknown provider' };
    }

    return { accepted: true, provider: name, branch, commit };
  }
}
