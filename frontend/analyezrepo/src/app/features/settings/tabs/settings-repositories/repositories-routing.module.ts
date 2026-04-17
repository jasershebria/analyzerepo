import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SettingsRepositoriesComponent } from './settings-repositories.component';
import { AddRepositoryComponent } from './add-repository/add-repository.component';

const routes: Routes = [
  { path: '',    component: SettingsRepositoriesComponent },
  { path: 'add', component: AddRepositoryComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class RepositoriesRoutingModule {}
