import { IsBoolean, IsNotEmpty, IsOptional, IsString, IsUrl, Matches } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class ProviderDto {
  id: string;
  name: string;
  code: string;
  apiBaseUrl: string;
  isActive: boolean;
  createdAt: Date;
}

export class CreateProviderDto {
  @ApiProperty()
  @IsString()
  @IsNotEmpty()
  name: string;

  @ApiProperty({ description: 'Lowercase alphanumeric, e.g. "github"' })
  @IsString()
  @Matches(/^[a-z0-9_-]+$/, { message: 'code must be lowercase alphanumeric' })
  code: string;

  @ApiProperty()
  @IsUrl()
  apiBaseUrl: string;
}

export class GetAllProvidersQuery {
  @ApiPropertyOptional({ default: 1 })
  pageIndex?: number = 1;

  @ApiPropertyOptional({ default: 50 })
  maxResultCount?: number = 50;

  @ApiPropertyOptional()
  @IsOptional()
  searchTerm?: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsBoolean()
  isActive?: boolean;
}
