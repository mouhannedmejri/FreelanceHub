import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { SellerDashboardPage } from './seller-dashboard.page';

const routes: Routes = [
  {
    path: '',
    component: SellerDashboardPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class SellerDashboardPageRoutingModule {}
