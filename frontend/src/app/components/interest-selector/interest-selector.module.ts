import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InterestSelectorComponent } from './interest-selector.component';

@NgModule({
  declarations: [InterestSelectorComponent],
  imports: [CommonModule],
  exports: [InterestSelectorComponent],
})
export class InterestSelectorModule {}
