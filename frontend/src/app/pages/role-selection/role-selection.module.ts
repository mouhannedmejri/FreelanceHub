import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { RouterModule, Routes } from '@angular/router';
import { RoleSelectionPage } from './role-selection.page';

const routes: Routes = [
  { path: '', component: RoleSelectionPage },
];

@NgModule({
  imports: [CommonModule, FormsModule, IonicModule, RouterModule.forChild(routes)],
  declarations: [RoleSelectionPage],
})
export class RoleSelectionPageModule {}
