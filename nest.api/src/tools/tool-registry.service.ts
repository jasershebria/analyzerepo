import { Injectable } from '@nestjs/common';
import { BaseTool } from './base/base-tool';
import { FileReadTool } from './file-read.tool';
import { FileWriteTool } from './file-write.tool';
import { FileEditTool } from './file-edit.tool';
import { GlobTool } from './glob.tool';
import { GrepTool } from './grep.tool';
import { BashTool } from './bash.tool';
import { TodoWriteTool } from './todo-write.tool';
import { WebFetchTool } from './web-fetch.tool';
import { WebSearchTool } from './web-search.tool';
import { RagSearchTool, RagSearchFn } from './rag-search.tool';

@Injectable()
export class ToolRegistryService {
  getAll(workingDir?: string, ragSearchFn?: RagSearchFn): BaseTool[] {
    return [
      new FileReadTool(workingDir),
      new FileWriteTool(workingDir),
      new FileEditTool(workingDir),
      new GlobTool(workingDir),
      new GrepTool(workingDir),
      new BashTool(workingDir),
      new TodoWriteTool(workingDir),
      new WebFetchTool(workingDir),
      new WebSearchTool(workingDir),
      new RagSearchTool(workingDir, ragSearchFn),
    ];
  }

  getRegistry(workingDir?: string, ragSearchFn?: RagSearchFn): Record<string, BaseTool> {
    return Object.fromEntries(this.getAll(workingDir, ragSearchFn).map((t) => [t.name, t]));
  }
}
