import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { StorePage } from './store.page';
import { StorePageRoutingModule } from './store-routing.module';

@NgModule({
    imports: [CommonModule, IonicModule, StorePageRoutingModule],
    declarations: [StorePage],
})
export class StorePageModule { }
