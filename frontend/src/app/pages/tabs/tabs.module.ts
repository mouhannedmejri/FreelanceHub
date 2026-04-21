import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { TabsPage } from './tabs.page';
import { TabsPageRoutingModule } from './tabs-routing.module';

@NgModule({
  imports: [CommonModule, IonicModule, TabsPageRoutingModule],
  declarations: [TabsPage],
})
export class TabsPageModule {}
