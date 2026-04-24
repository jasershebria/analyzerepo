import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, shareReplay } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface Skill {
  name: string;
  description: string;
  prompt: string;
}

@Injectable({ providedIn: 'root' })
export class SkillsService {
  private readonly http = inject(HttpClient);
  private readonly url = `${environment.apiBase}/api/agent/skills`;

  private skills$: Observable<Skill[]> | null = null;

  getSkills(): Observable<Skill[]> {
    if (!this.skills$) {
      this.skills$ = this.http.get<Skill[]>(this.url).pipe(shareReplay(1));
    }
    return this.skills$;
  }
}
