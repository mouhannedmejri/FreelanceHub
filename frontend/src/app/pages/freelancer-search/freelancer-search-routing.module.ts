import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { FreelancerSearchPage } from './freelancer-search.page';

const routes: Routes = [
  {
    path: '',
    component: FreelancerSearchPage,
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class FreelancerSearchPageRoutingModule {}
