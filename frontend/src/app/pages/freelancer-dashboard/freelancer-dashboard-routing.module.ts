import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { FreelancerDashboardPage } from './freelancer-dashboard.page';

const routes: Routes = [
  {
    path: '',
    component: FreelancerDashboardPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class FreelancerDashboardPageRoutingModule {}
