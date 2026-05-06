import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { OnboardingPageRoutingModule } from './onboarding-routing.module';
import { OnboardingPage } from './onboarding.page';
import { InterestSelectorModule } from '../../components/interest-selector/interest-selector.module';

@NgModule({
  imports: [CommonModule, FormsModule, IonicModule, OnboardingPageRoutingModule, InterestSelectorModule],
  declarations: [OnboardingPage],
})
export class OnboardingPageModule {}
