import { Body, Controller, Delete, Get, HttpCode, HttpStatus, Param, Post, Query } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { ProvidersService } from './providers.service';
import { CreateProviderDto, GetAllProvidersQuery } from './dto/provider.dto';

@ApiTags('Providers')
@Controller('api/providers')
export class ProvidersController {
  constructor(private readonly svc: ProvidersService) {}

  @Get()
  @ApiOperation({ summary: 'Get all providers' })
  getAll(@Query() query: GetAllProvidersQuery) {
    return this.svc.getAll(query);
  }

  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Create a new provider' })
  create(@Body() dto: CreateProviderDto) {
    return this.svc.create(dto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ summary: 'Delete a provider' })
  delete(@Param('id') id: string) {
    return this.svc.delete(id);
  }
}
