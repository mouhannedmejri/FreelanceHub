import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { GuestBannerComponent } from './guest-banner/guest-banner.component';
import { AuthModalComponent } from './auth-modal/auth-modal.component';

@NgModule({
  declarations: [GuestBannerComponent, AuthModalComponent],
  imports: [CommonModule, FormsModule, IonicModule],
  exports: [GuestBannerComponent, AuthModalComponent],
})
export class SharedComponentsModule {}
