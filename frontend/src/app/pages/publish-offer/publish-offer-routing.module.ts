import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { PublishOfferPage } from './publish-offer.page';

const routes: Routes = [
  {
    path: '',
    component: PublishOfferPage,
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class PublishOfferPageRoutingModule {}
