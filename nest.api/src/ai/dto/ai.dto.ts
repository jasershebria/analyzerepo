import { IsArray, IsOptional, IsString } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class ChatMessageDto {
  @ApiProperty({ enum: ['system', 'user', 'assistant'] })
  @IsString()
  role: 'system' | 'user' | 'assistant';

  @ApiProperty()
  @IsString()
  content: string;
}

export class ChatWithHistoryDto {
  @ApiProperty({ type: [ChatMessageDto] })
  @IsArray()
  messages: ChatMessageDto[];

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  systemPrompt?: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  repoId?: string;
}
