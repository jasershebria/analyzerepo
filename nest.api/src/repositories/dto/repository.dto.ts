import { IsArray, IsBoolean, IsInt, IsNotEmpty, IsOptional, IsString, IsUrl, IsUUID, Min } from 'class-validator';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { Type } from 'class-transformer';

export class RepositoryDto {
  id: string;
  name: string;
  webUrl: string;
  cloneUrl: string | null;
  defaultBranch: string;
  providerId: string;
  providerRepoId: string | null;
  isActive: boolean;
  clonedDirectory: string | null;
  createdAt: Date;
}

export class AuthDto {
  authType: number;
  secretRef: string | null;
}

export class BranchRuleDto {
  pattern: string;
  isEnabled: boolean;
  scanOnPush: boolean;
}

export class GetRepositoryResponse extends RepositoryDto {
  auth: AuthDto | null;
  branchRules: BranchRuleDto[];
}

export class BranchRuleInput {
  @IsString() pattern: string;
  @IsBoolean() @IsOptional() scanOnPush?: boolean = false;
}

export class CreateRepositoryDto {
  @ApiProperty() @IsUUID() providerId: string;
  @ApiPropertyOptional() @IsOptional() @IsString() providerRepoId?: string;
  @ApiProperty() @IsString() @IsNotEmpty() name: string;
  @ApiProperty() @IsUrl() webUrl: string;
  @ApiPropertyOptional() @IsOptional() @IsString() cloneUrl?: string;
  @ApiPropertyOptional() @IsOptional() @IsString() defaultBranch?: string = 'main';
  @ApiProperty({ enum: [1, 2, 3] }) @IsInt() authType: number;
  @ApiPropertyOptional() @IsOptional() @IsString() secretRef?: string;
  @ApiPropertyOptional() @IsOptional() @IsBoolean() runInitialScan?: boolean = false;
  @ApiPropertyOptional({ type: [BranchRuleInput] })
  @IsOptional()
  @IsArray()
  @Type(() => BranchRuleInput)
  branchRules?: BranchRuleInput[] = [];
}

export class UpdateRepositoryDto {
  @ApiPropertyOptional() @IsOptional() @IsString() name?: string;
  @ApiPropertyOptional() @IsOptional() @IsString() defaultBranch?: string;
  @ApiPropertyOptional() @IsOptional() @IsBoolean() isActive?: boolean;
  @ApiPropertyOptional() @IsOptional() @IsString() secretRef?: string;
  @ApiPropertyOptional({ type: [BranchRuleInput] })
  @IsOptional()
  @IsArray()
  @Type(() => BranchRuleInput)
  branchRules?: BranchRuleInput[];
}

export class TestConnectionDto {
  @ApiProperty() @IsUUID() providerId: string;
  @ApiProperty() @IsUrl() webUrl: string;
  @ApiProperty({ enum: [1, 2, 3] }) @IsInt() authType: number;
  @ApiPropertyOptional() @IsOptional() @IsString() secretRef?: string;
}

export class TestConnectionResponse {
  success: boolean;
  repoName?: string;
  providerRepoId?: string;
  defaultBranch?: string;
  branches?: string[];
  errorMessage?: string;
}

export class GetAllRepositoriesQuery {
  @ApiPropertyOptional({ default: 1 }) @IsOptional() @Type(() => Number) pageIndex?: number = 1;
  @ApiPropertyOptional({ default: 0 }) @IsOptional() @Type(() => Number) skipCount?: number = 0;
  @ApiPropertyOptional({ default: 10 }) @IsOptional() @Type(() => Number) maxResultCount?: number = 10;
  @ApiPropertyOptional() @IsOptional() searchTerm?: string;
  @ApiPropertyOptional() @IsOptional() providerId?: string;
  @ApiPropertyOptional() @IsOptional() @Type(() => Boolean) isActive?: boolean;
  @ApiPropertyOptional() @IsOptional() @Type(() => Boolean) includeDeleted?: boolean = false;
}
