import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DigitalStorePage } from './digital-store.page';

const routes: Routes = [
  {
    path: '',
    component: DigitalStorePage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class DigitalStorePageRoutingModule {}
