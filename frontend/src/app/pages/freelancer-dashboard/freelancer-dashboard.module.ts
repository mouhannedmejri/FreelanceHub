import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { FreelancerDashboardPageRoutingModule } from './freelancer-dashboard-routing.module';

import { FreelancerDashboardPage } from './freelancer-dashboard.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    FreelancerDashboardPageRoutingModule
  ],
  declarations: [FreelancerDashboardPage]
})
export class FreelancerDashboardPageModule {}
