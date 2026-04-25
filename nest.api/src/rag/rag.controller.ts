import { Body, Controller, Post } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { RagService } from './rag.service';
import { QueryRagDto } from './dto/rag.dto';

@ApiTags('RAG')
@Controller('api/rag')
export class RagController {
  constructor(private readonly svc: RagService) {}

  @Post('query')
  @ApiOperation({ summary: 'Query indexed repository code with semantic search + LLM synthesis' })
  query(@Body() dto: QueryRagDto) {
    return this.svc.query(dto);
  }
}
