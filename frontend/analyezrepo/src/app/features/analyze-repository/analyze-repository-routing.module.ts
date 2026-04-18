import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AnalyzeRepositoryComponent } from './analyze-repository.component';
import { RepoSessionComponent } from './components/repo-session/repo-session.component';

const routes: Routes = [
  { path: '', component: AnalyzeRepositoryComponent },
  { path: ':id', component: RepoSessionComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AnalyzeRepositoryRoutingModule {}
