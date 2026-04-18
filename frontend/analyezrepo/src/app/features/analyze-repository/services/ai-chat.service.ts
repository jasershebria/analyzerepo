import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AiChatHistoryRequest, AiChatResponse } from '../../../models/analysis.models';
import { environment } from '../../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AiChatService {
  private readonly http = inject(HttpClient);

  chatWithHistory(request: AiChatHistoryRequest): Observable<AiChatResponse> {
    return this.http.post<AiChatResponse>(
      `${environment.apiBase}/api/ai/chat/history`,
      request
    );
  }
}
