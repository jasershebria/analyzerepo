import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SettingsComponent } from './settings.component';
import { SettingsGithubComponent } from './tabs/settings-github/settings-github.component';
import { SettingsApiComponent } from './tabs/settings-api/settings-api.component';
import { SettingsNotificationsComponent } from './tabs/settings-notifications/settings-notifications.component';
import { SettingsAppearanceComponent } from './tabs/settings-appearance/settings-appearance.component';

const routes: Routes = [
  {
    path: '',
    component: SettingsComponent,
    children: [
      { path: '', redirectTo: 'repositories', pathMatch: 'full' },
      {
        path: 'repositories',
        loadChildren: () =>
          import('./tabs/settings-repositories/repositories.module').then(
            (m) => m.RepositoriesModule
          ),
      },
      {
        path: 'providers',
        loadChildren: () =>
          import('./tabs/settings-providers/providers.module').then(
            (m) => m.ProvidersModule
          ),
      },
      { path: 'github',        component: SettingsGithubComponent },
      { path: 'api',           component: SettingsApiComponent },
      { path: 'notifications', component: SettingsNotificationsComponent },
      { path: 'appearance',    component: SettingsAppearanceComponent },
    ],
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class SettingsRoutingModule {}
