import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AnalyzeRepositoryComponent } from './analyze-repository.component';

const routes: Routes = [{ path: '', component: AnalyzeRepositoryComponent }];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AnalyzeRepositoryRoutingModule {}
