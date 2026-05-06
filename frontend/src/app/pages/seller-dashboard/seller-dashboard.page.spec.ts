import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SellerDashboardPage } from './seller-dashboard.page';

describe('SellerDashboardPage', () => {
  let component: SellerDashboardPage;
  let fixture: ComponentFixture<SellerDashboardPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(SellerDashboardPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
