import { ConfigService } from '@nestjs/config';
import { MongooseModuleOptions } from '@nestjs/mongoose';

export const mongooseConfig = (config: ConfigService): MongooseModuleOptions => ({
  uri: config.get<string>('mongodb.url'),
  dbName: config.get<string>('mongodb.db'),
});
