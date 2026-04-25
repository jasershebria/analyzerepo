import { Column, Entity, PrimaryGeneratedColumn } from 'typeorm';
import { AuditMixin } from '../../database/audit.mixin';

@Entity('SourceProviders')
export class SourceProvider extends AuditMixin {
  @PrimaryGeneratedColumn('uuid', { name: 'Id' })
  id: string;

  @Column({ name: 'Name', length: 200 })
  name: string;

  @Column({ name: 'Code', length: 50, unique: true })
  code: string;

  @Column({ name: 'ApiBaseUrl', length: 500 })
  apiBaseUrl: string;

  @Column({ name: 'IsActive', default: true })
  isActive: boolean;
}
