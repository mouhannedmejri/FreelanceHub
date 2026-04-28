import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FreelancerDashboardPage } from './freelancer-dashboard.page';

describe('FreelancerDashboardPage', () => {
  let component: FreelancerDashboardPage;
  let fixture: ComponentFixture<FreelancerDashboardPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(FreelancerDashboardPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
