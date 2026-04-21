import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { PublishOfferPage } from './publish-offer.page';
import { PublishOfferPageRoutingModule } from './publish-offer-routing.module';

@NgModule({
  imports: [CommonModule, FormsModule, IonicModule, PublishOfferPageRoutingModule],
  declarations: [PublishOfferPage],
})
export class PublishOfferPageModule {}
