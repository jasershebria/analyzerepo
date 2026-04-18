import { NgModule } from '@angular/core';
import { ProvidersRoutingModule } from './providers-routing.module';
import { SettingsProvidersComponent } from './settings-providers.component';
import { AddProviderModalComponent } from './components/add-provider-modal/add-provider-modal.component';
import { SharedModule } from '../../../../shared/shared.module';

@NgModule({
  declarations: [
    SettingsProvidersComponent,
    AddProviderModalComponent,
  ],
  imports: [SharedModule, ProvidersRoutingModule],
})
export class ProvidersModule {}
