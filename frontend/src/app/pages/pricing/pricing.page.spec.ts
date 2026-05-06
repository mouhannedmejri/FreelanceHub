import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PricingPage } from './pricing.page';

describe('PricingPage', () => {
  let component: PricingPage;
  let fixture: ComponentFixture<PricingPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(PricingPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
