import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { SellerDashboardPageRoutingModule } from './seller-dashboard-routing.module';

import { SellerDashboardPage } from './seller-dashboard.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    SellerDashboardPageRoutingModule
  ],
  declarations: [SellerDashboardPage]
})
export class SellerDashboardPageModule {}
