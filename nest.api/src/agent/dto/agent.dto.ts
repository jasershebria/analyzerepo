import { IsArray, IsNumber, IsOptional, IsString } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class AgentMessageDto {
  @ApiProperty({ enum: ['user', 'assistant', 'system'] })
  @IsString()
  role: string;

  @ApiProperty()
  @IsString()
  content: string;
}

export class AgentRunDto {
  @ApiProperty()
  @IsString()
  prompt: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  repoId?: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  clonedPath?: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  systemPrompt?: string;

  @ApiPropertyOptional({ type: [AgentMessageDto] })
  @IsOptional()
  @IsArray()
  history?: AgentMessageDto[];

  @ApiPropertyOptional({ default: 15 })
  @IsOptional()
  @IsNumber()
  maxRounds?: number = 15;
}

export class SkillDto {
  name: string;
  description: string;
  prompt: string;
}
