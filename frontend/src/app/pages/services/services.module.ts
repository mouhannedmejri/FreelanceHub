import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { ServicesPage } from './services.page';
import { ServicesPageRoutingModule } from './services-routing.module';

@NgModule({
  imports: [CommonModule, FormsModule, IonicModule, ServicesPageRoutingModule],
  declarations: [ServicesPage],
})
export class ServicesPageModule {}
