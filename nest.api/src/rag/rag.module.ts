import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { RagController } from './rag.controller';
import { RagService } from './rag.service';
import { VectorStoreService } from './vector-store.service';
import { IndexingService } from './indexing.service';
import { AiModule } from '../ai/ai.module';

@Module({
  imports: [MongooseModule.forFeature([]), AiModule],
  controllers: [RagController],
  providers: [RagService, VectorStoreService, IndexingService],
  exports: [RagService, VectorStoreService, IndexingService],
})
export class RagModule {}
