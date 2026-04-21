import { ComponentFixture, TestBed } from '@angular/core/testing';
import { OfferProposalsPage } from './offer-proposals.page';

describe('OfferProposalsPage', () => {
  let component: OfferProposalsPage;
  let fixture: ComponentFixture<OfferProposalsPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(OfferProposalsPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
