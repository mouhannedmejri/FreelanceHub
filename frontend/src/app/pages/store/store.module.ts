import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { RouterModule } from '@angular/router';
import { StorePage } from './store.page';
import { StorePageRoutingModule } from './store-routing.module';

@NgModule({
  imports: [CommonModule, FormsModule, IonicModule, RouterModule, StorePageRoutingModule],
  declarations: [StorePage],
})
export class StorePageModule {}
