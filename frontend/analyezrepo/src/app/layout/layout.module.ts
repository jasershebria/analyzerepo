import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';
import { LayoutComponent } from './layout.component';
import { SidebarComponent } from './sidebar/sidebar.component';
import { SharedModule } from '../shared/shared.module';

@NgModule({
  declarations: [LayoutComponent, SidebarComponent],
  imports: [SharedModule, RouterModule],
  exports: [LayoutComponent],
})
export class LayoutModule {}
