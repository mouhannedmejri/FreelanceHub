import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { OfferProposalsPageRoutingModule } from './offer-proposals-routing.module';

import { OfferProposalsPage } from './offer-proposals.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    OfferProposalsPageRoutingModule
  ],
  declarations: [OfferProposalsPage]
})
export class OfferProposalsPageModule {}
