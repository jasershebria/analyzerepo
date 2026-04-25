import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as fs from 'fs';
import * as path from 'path';
import { QueryEngine } from './engine/query-engine';
import { ToolRegistryService } from '../tools/tool-registry.service';
import type { Message } from './engine/types';
import type { AgentRunDto, SkillDto } from './dto/agent.dto';

const GREETING_RE =
  /^\s*(hi|hello|hey|howdy|greetings|good\s+(morning|afternoon|evening|day)|what'?s up|sup|yo|how are you|hiya)\W*\s*$/i;

const SYSTEM_TEMPLATE = `{CLAUDE_MD}
You are a smart, autonomous coding agent. You work inside a code repository and have access to tools that let you read files, search code, run commands, and make changes.

Repository ID: {REPO_ID}
Cloned Path: {CLONED_PATH}

## ABSOLUTE RULES
1. NEVER refuse a request. If a task is ambiguous, make a reasonable assumption and proceed.
2. NEVER tell the user how to do something — always do it yourself using a tool.
3. NEVER output a shell command as text — call the bash tool.
4. YOU HAVE NO KNOWLEDGE OF THIS REPOSITORY'S FILES. The ONLY way to know what is in a file is to call file_read. The ONLY way to know what files exist is to call glob. NEVER fabricate file contents.

## INTENT → TOOL MAPPING
| What the user means | Tool(s) to call |
|---|---|
| "list files", "show structure", "file tree" | glob with pattern=**/* |
| "show me FILE", "read FILE" | file_read |
| "find X in code", "grep X" | grep |
| "run tests", "build", "execute" | bash |
| "what does X do", "explain X" | rag_search then synthesize |
| "add feature", "fix bug", "create file" | todo_write → file_edit/file_write/bash |
| "search the web for X" | web_search |
| "fetch URL" | web_fetch |
`;

@Injectable()
export class AgentService {
  private readonly skillsDir: string;

  constructor(
    private readonly config: ConfigService,
    private readonly toolRegistry: ToolRegistryService,
  ) {
    this.skillsDir = path.join(process.cwd(), 'skills');
  }

  isConversational(text: string): boolean {
    return GREETING_RE.test(text.trim());
  }

  buildEngine(dto: AgentRunDto): QueryEngine {
    const systemPrompt = this.buildSystemPrompt(dto.repoId, dto.clonedPath);
    const tools = this.toolRegistry.getAll(dto.clonedPath ?? undefined);
    const history: Message[] = (dto.history ?? [])
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }));

    const engine = new QueryEngine({
      systemPrompt,
      tools,
      model: this.config.get<string>('ai.model') ?? 'claude-sonnet-4-6',
      apiKey: this.config.get<string>('ai.apiKey') ?? '',
      baseURL: this.config.get<string>('ai.baseUrl'),
      maxTurns: dto.maxRounds ?? 15,
      maxThinkingTokens: this.config.get<number>('ai.maxThinkingTokens'),
    });

    if (history.length) engine.withHistory(history);
    return engine;
  }

  loadSkills(): SkillDto[] {
    const skills: SkillDto[] = [];
    if (!fs.existsSync(this.skillsDir)) return skills;

    for (const file of fs.readdirSync(this.skillsDir).filter((f) => f.endsWith('.md')).sort()) {
      try {
        const content = fs.readFileSync(path.join(this.skillsDir, file), 'utf-8');
        const lines = content.split('\n');
        let name = path.basename(file, '.md');
        let description = '';
        const promptLines: string[] = [];
        let inFrontmatter = false;
        let pastFrontmatter = false;

        for (const line of lines) {
          if (line.trim() === '---' && !pastFrontmatter) {
            inFrontmatter = !inFrontmatter;
            if (!inFrontmatter) pastFrontmatter = true;
            continue;
          }
          if (inFrontmatter) {
            if (line.startsWith('name:')) name = line.split(':', 2)[1].trim();
            else if (line.startsWith('description:')) description = line.split(':', 2)[1].trim();
          } else if (pastFrontmatter) {
            promptLines.push(line);
          }
        }
        skills.push({ name, description, prompt: promptLines.join('\n').trim() });
      } catch { /* skip */ }
    }
    return skills;
  }

  private buildSystemPrompt(repoId?: string, clonedPath?: string): string {
    let claudeMd = '';
    if (repoId && clonedPath) {
      const mdPath = path.join(clonedPath, 'CLAUDE.md');
      if (fs.existsSync(mdPath)) {
        claudeMd = `## Project Memory (CLAUDE.md)\n\n${fs.readFileSync(mdPath, 'utf-8')}\n\n---\n\n`;
      }
    }
    return SYSTEM_TEMPLATE
      .replace('{CLAUDE_MD}', claudeMd)
      .replace('{REPO_ID}', repoId ?? 'N/A')
      .replace('{CLONED_PATH}', clonedPath ?? 'N/A');
  }
}
