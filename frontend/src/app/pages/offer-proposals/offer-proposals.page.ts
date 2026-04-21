import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ProposalService } from '../../services/proposal.service';
import { AlertController, ToastController } from '@ionic/angular';

@Component({
  selector: 'app-offer-proposals',
  templateUrl: './offer-proposals.page.html',
  styleUrls: ['./offer-proposals.page.scss'],
  standalone: false,
})
export class OfferProposalsPage implements OnInit {
  offerId: number | null = null;
  proposals: any[] = [];
  isLoading = false;

  constructor(
    private route: ActivatedRoute,
    private proposalService: ProposalService,
    private alertController: AlertController,
    private toastController: ToastController,
    private router: Router
  ) {}

  ngOnInit() {
    this.offerId = Number(this.route.snapshot.paramMap.get('id'));
    if (this.offerId) {
      this.loadProposals();
    }
  }

  doRefresh(event: any) {
    this.loadProposals(event);
  }

  loadProposals(event?: any) {
    if (!this.offerId) return;
    this.isLoading = true;
    this.proposalService.getOfferProposals(this.offerId).subscribe({
      next: (res) => {
        this.proposals = res.proposals;
        this.isLoading = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoading = false;
        if (event) event.target.complete();
      }
    });
  }

  viewProfile(freelancerId: number) {
    this.router.navigate(['/home/tabs/profile', freelancerId]);
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
              next: async () => {
                const toast = await this.toastController.create({
                  message: `Proposition ${status === 'accepted' ? 'acceptée' : 'refusée'} avec succès`,
                  duration: 2000, color: status === 'accepted' ? 'success' : 'medium'
                });
                toast.present();
                this.loadProposals();
              }
            });
          } 
        }
      ]
    });
    await alert.present();
  }
}
