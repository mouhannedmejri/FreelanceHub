import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { DigitalStorePageRoutingModule } from './digital-store-routing.module';
import { DigitalStorePage } from './digital-store.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    DigitalStorePageRoutingModule
  ],
  declarations: [DigitalStorePage]
})
export class DigitalStorePageModule {}
