import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { MyPurchasesPage } from './my-purchases.page';

const routes: Routes = [
  {
    path: '',
    component: MyPurchasesPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class MyPurchasesPageRoutingModule {}
