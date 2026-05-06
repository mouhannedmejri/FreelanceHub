import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';

import { FreelancerSearchPageRoutingModule } from './freelancer-search-routing.module';
import { FreelancerSearchPage } from './freelancer-search.page';
import { FreelancerCardComponent } from '../../components/freelancer-card/freelancer-card.component';

@NgModule({
  imports: [CommonModule, FormsModule, IonicModule, FreelancerSearchPageRoutingModule],
  declarations: [FreelancerSearchPage, FreelancerCardComponent],
})
export class FreelancerSearchPageModule {}
