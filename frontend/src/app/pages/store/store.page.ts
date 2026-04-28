import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { OfferService } from '../../services/offer.service';
import { Offer } from '../../models/offer.model';
import { User } from '../../models/user.model';
import { Subscription, Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { ProposalService } from '../../services/proposal.service';
import { ToastController, AlertController } from '@ionic/angular';

@Component({
  selector: 'app-store',
  templateUrl: './store.page.html',
  styleUrls: ['./store.page.scss'],
  standalone: false,
})
export class StorePage implements OnInit, OnDestroy {
  user: User | null = null;
  offers: Offer[] = [];
  totalOffers = 0;
  isLoading = false;
  filterParams: { [key: string]: any } = {
    search: '',
    category: '',
    location: '',
    duration: '',
    budget_min: null,
    budget_max: null
  };
  
  isFilterModalOpen = false;

  private searchSubject = new Subject<string>();
  private subs: Subscription[] = [];
  
  // Pagination
  allOffers: Offer[] = [];
  displayedOffers: Offer[] = [];
  page = 1;
  pageSize = 10;
  hasMore = true;

  constructor(
    private authService: AuthService,
    private offerService: OfferService,
    private proposalService: ProposalService,
    private toastController: ToastController,
    private alertController: AlertController,
    private router: Router
  ) {}

  ngOnInit() {
    this.subs.push(
      this.authService.currentUser$.subscribe((user) => {
        this.user = user;
        this.loadOffers();
      })
    );
    
    this.subs.push(
      this.searchSubject.pipe(
        debounceTime(400),
        distinctUntilChanged()
      ).subscribe(searchTerm => {
        this.filterParams['search'] = searchTerm;
        this.loadOffers();
      })
    );
  }

  ngOnDestroy() {
    this.subs.forEach((s) => s.unsubscribe());
  }

  get isClient(): boolean {
    return this.user?.role === 'client';
  }

  get activeFilterCount(): number {
    return Object.values(this.filterParams).filter(
      v => v !== null && v !== '' && v !== undefined
    ).length;
  }

  doRefresh(event: any) {
    this.loadOffers(event);
  }

  loadOffers(event?: any) {
    if (this.isLoading && !event) return;
    this.isLoading = true;
    this.page = 1;

    const call = this.isClient
      ? this.offerService.getMyOffers(this.filterParams)
      : this.offerService.getOffers(this.filterParams);

    call.subscribe({
      next: (data) => {
        this.allOffers = data.offers;
        this.totalOffers = data.total;
        this.updateDisplayedOffers();
        this.isLoading = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoading = false;
        if (event) event.target.complete();
      },
    });
  }

  updateDisplayedOffers() {
    this.displayedOffers = this.allOffers.slice(0, this.page * this.pageSize);
    this.hasMore = this.displayedOffers.length < this.allOffers.length;
  }

  loadMore(event: any) {
    this.page++;
    this.updateDisplayedOffers();
    event.target.complete();
    if (!this.hasMore) {
      event.target.disabled = true;
    }
  }

  onSearch() {
    this.searchSubject.next(this.filterParams['search']);
  }

  openFilterModal() {
    this.isFilterModalOpen = true;
  }

  closeFilterModal() {
    this.isFilterModalOpen = false;
  }

  applyFilters() {
    this.isFilterModalOpen = false;
    this.loadOffers();
  }

  resetFilters() {
    this.filterParams = {
      search: this.filterParams['search'], // Keep search term
      category: '',
      location: '',
      duration: '',
      budget_min: null,
      budget_max: null
    };
    this.applyFilters();
  }

  toggleFilterCategory(cat: string) {
    this.filterParams['category'] = this.filterParams['category'] === cat ? '' : cat;
  }

  toggleFilterLocation(loc: string) {
    this.filterParams['location'] = this.filterParams['location'] === loc ? '' : loc;
  }

  toggleFilterDuration(dur: string) {
    this.filterParams['duration'] = this.filterParams['duration'] === dur ? '' : dur;
  }

  navigateToPublish() {
    this.router.navigate(['/publish-offer']);
  }

  getBudgetLabel(offer: Offer): string {
    if (offer.budget_min === 0 && offer.budget_max === 0) return 'Budget non précisé';
    if (offer.budget_min === offer.budget_max) return `${offer.budget_min}€`;
    return `${offer.budget_min}€ – ${offer.budget_max}€`;
  }

  getLocationIcon(location: string): string {
    switch (location) {
      case 'Remote': return 'globe-outline';
      case 'Hybrid': return 'git-network-outline';
      case 'Onsite': return 'business-outline';
      default: return 'location-outline';
    }
  }

  getLocationLabel(location: string): string {
    switch (location) {
      case 'Remote': return 'Remote';
      case 'Hybrid': return 'Hybride';
      case 'Onsite': return 'Sur site';
      default: return location;
    }
  }

  getCategoryColor(category: string): string {
    switch (category) {
      case 'Développement': return 'cat-dev';
      case 'Design': return 'cat-design';
      case 'Marketing': return 'cat-marketing';
      case 'Rédaction': return 'cat-redaction';
      default: return '';
    }
  }

  // Proposals Logic
  isApplyModalOpen = false;
  isProposalsModalOpen = false;
  selectedOffer: Offer | null = null;
  proposalData = { cover_letter: '', proposed_price: 0, estimated_duration: '1 à 2 semaines' };
  
  proposals: any[] = [];
  isLoadingProposals = false;

  applyForOffer(offer: Offer) {
    this.selectedOffer = offer;
    this.proposalData = { cover_letter: '', proposed_price: offer.budget_min || 0, estimated_duration: '1 à 2 semaines' };
    this.isApplyModalOpen = true;
  }

  submitProposal() {
    if (!this.selectedOffer) return;
    this.proposalService.submitProposal(this.selectedOffer.id, this.proposalData).subscribe({
      next: async () => {
        this.isApplyModalOpen = false;
        const toast = await this.toastController.create({
          message: 'Proposition envoyée avec succès !',
          duration: 3000, color: 'success'
        });
        toast.present();
        this.loadOffers(); // refresh offers to update count
      },
      error: async (err) => {
        const toast = await this.toastController.create({
          message: 'Erreur lors de l\'envoi de la proposition.',
          duration: 3000, color: 'danger'
        });
        toast.present();
      }
    });
  }

  viewProposals(offer: Offer) {
    this.router.navigate(['/offer-proposals', offer.id]);
  }

  updateProposal(proposal: any, status: 'accepted' | 'rejected') {
    this.proposalService.updateProposal(proposal.id, status).subscribe({
      next: () => {
        proposal.status = status;
        this.toastController.create({
          message: status === 'accepted' ? 'Proposition acceptée' : 'Proposition refusée',
          duration: 2000,
          color: status === 'accepted' ? 'success' : 'medium'
        }).then(t => t.present());
      },
      error: (err: any) => console.error(err)
    });
  }
}
