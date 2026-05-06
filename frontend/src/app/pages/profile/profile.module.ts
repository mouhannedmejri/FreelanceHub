import { CUSTOM_ELEMENTS_SCHEMA, NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { ProfilePage } from './profile.page';
import { ProfilePageRoutingModule } from './profile-routing.module';
import { InterestSelectorModule } from '../../components/interest-selector/interest-selector.module';
import { PortfolioGridComponent } from '../../components/portfolio-grid/portfolio-grid.component';
import { AddPortfolioProjectModalComponent } from '../../components/add-portfolio-project-modal/add-portfolio-project-modal.component';

@NgModule({
  imports: [CommonModule, FormsModule, IonicModule, ProfilePageRoutingModule, InterestSelectorModule],
  declarations: [ProfilePage, PortfolioGridComponent, AddPortfolioProjectModalComponent],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
})
export class ProfilePageModule {}
