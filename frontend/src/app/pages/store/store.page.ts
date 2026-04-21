import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { OfferService } from '../../services/offer.service';
import { Offer } from '../../models/offer.model';
import { User } from '../../models/user.model';
import { Subscription } from 'rxjs';
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
  searchTerm = '';
  private subs: Subscription[] = [];
  private searchTimeout: any;

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
  }

  ngOnDestroy() {
    this.subs.forEach((s) => s.unsubscribe());
  }

  get isClient(): boolean {
    return this.user?.role === 'client';
  }

  loadOffers() {
    if (this.isLoading) return;
    this.isLoading = true;

    const call = this.isClient
      ? this.offerService.getMyOffers()
      : this.offerService.getOffers(this.searchTerm);

    call.subscribe({
      next: (data) => {
        this.offers = data.offers;
        this.totalOffers = data.total;
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      },
    });
  }

  onSearch() {
    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(() => {
      this.loadOffers();
    }, 300);
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
    this.selectedOffer = offer;
    this.isProposalsModalOpen = true;
    this.loadProposals();
  }

  loadProposals() {
    if (!this.selectedOffer) return;
    this.isLoadingProposals = true;
    this.proposalService.getOfferProposals(this.selectedOffer.id).subscribe({
      next: (res) => {
        this.proposals = res.proposals;
        this.isLoadingProposals = false;
      },
      error: () => {
        this.isLoadingProposals = false;
      }
    });
  }

  async updateProposal(proposal: any, status: 'accepted' | 'rejected') {
    const alert = await this.alertController.create({
      header: 'Confirmation',
      message: `Êtes-vous sûr de vouloir ${status === 'accepted' ? 'accepter' : 'refuser'} cette proposition ?`,
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        { 
          text: 'Confirmer', 
          handler: () => {
            this.proposalService.updateProposalStatus(proposal.id, status).subscribe({
              next: () => {
                this.loadProposals();
                this.loadOffers();
              }
            });
          } 
        }
      ]
    });
    await alert.present();
  }
}
