import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { OfferProposalsPage } from './offer-proposals.page';

const routes: Routes = [
  {
    path: '',
    component: OfferProposalsPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class OfferProposalsPageRoutingModule {}
