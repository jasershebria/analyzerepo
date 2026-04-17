import { NgModule } from '@angular/core';
import { SettingsRoutingModule } from './settings-routing.module';
import { SettingsComponent } from './settings.component';
import { SettingsGithubComponent } from './tabs/settings-github/settings-github.component';
import { SettingsApiComponent } from './tabs/settings-api/settings-api.component';
import { SettingsNotificationsComponent } from './tabs/settings-notifications/settings-notifications.component';
import { SettingsAppearanceComponent } from './tabs/settings-appearance/settings-appearance.component';
import { SharedModule } from '../../shared/shared.module';

@NgModule({
  declarations: [
    SettingsComponent,
    SettingsGithubComponent,
    SettingsApiComponent,
    SettingsNotificationsComponent,
    SettingsAppearanceComponent,
  ],
  imports: [SharedModule, SettingsRoutingModule],
})
export class SettingsModule {}
