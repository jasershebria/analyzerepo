import { Module } from '@nestjs/common';
import { ProviderClientFactory } from './provider-client.factory';

@Module({
  providers: [ProviderClientFactory],
  exports: [ProviderClientFactory],
})
export class ProviderClientsModule {}
