import { NgModule } from '@angular/core';
import { RepositoriesRoutingModule } from './repositories-routing.module';
import { SettingsRepositoriesComponent } from './settings-repositories.component';
import { AddRepositoryComponent } from './components/add-repository/add-repository.component';
import { SharedModule } from '../../../../shared/shared.module';

@NgModule({
  declarations: [
    SettingsRepositoriesComponent,
    AddRepositoryComponent,
  ],
  imports: [SharedModule, RepositoriesRoutingModule],
})
export class RepositoriesModule {}
