import { ConfigService } from '@nestjs/config';
import { TypeOrmModuleOptions } from '@nestjs/typeorm';

export const typeOrmConfig = (config: ConfigService): TypeOrmModuleOptions => ({
  type: 'postgres',
  url: config.get<string>('database.url'),
  entities: [__dirname + '/../**/*.entity{.ts,.js}'],
  synchronize: false,
  logging: ['error'],
  extra: { max: 10 },
});
