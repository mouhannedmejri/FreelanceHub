import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ClientDashboardPage } from './client-dashboard.page';

describe('ClientDashboardPage', () => {
  let component: ClientDashboardPage;
  let fixture: ComponentFixture<ClientDashboardPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(ClientDashboardPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
