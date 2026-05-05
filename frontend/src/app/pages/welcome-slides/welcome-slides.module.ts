import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { RouterModule, Routes } from '@angular/router';
import { WelcomeSlidesPage } from './welcome-slides.page';

const routes: Routes = [
  { path: '', component: WelcomeSlidesPage },
];

@NgModule({
  imports: [CommonModule, FormsModule, IonicModule, RouterModule.forChild(routes)],
  declarations: [WelcomeSlidesPage],
})
export class WelcomeSlidesPageModule {}
