import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { AuthPageRoutingModule } from './auth-routing.module';
import { AuthPage } from './auth.page';
import { InterestSelectorModule } from '../../components/interest-selector/interest-selector.module';

@NgModule({
  imports: [CommonModule, FormsModule, IonicModule, AuthPageRoutingModule, InterestSelectorModule],
  declarations: [AuthPage],
})
export class AuthPageModule {}
