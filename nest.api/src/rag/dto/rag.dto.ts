import { IsNumber, IsOptional, IsString } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class QueryRagDto {
  @ApiProperty() @IsString() repoId: string;
  @ApiProperty() @IsString() question: string;
  @ApiPropertyOptional({ default: 5 }) @IsOptional() @IsNumber() topK?: number = 5;
}

export class SourceReference {
  filePath: string;
  score: number;
}

export class QueryRagResponse {
  answer: string;
  sources: SourceReference[];
}
