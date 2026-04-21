import { Component, OnInit } from '@angular/core';
import { AdminService } from '../../services/admin.service';
import { ToastController, AlertController } from '@ionic/angular';

@Component({
  selector: 'app-admin-dashboard',
  templateUrl: './admin-dashboard.page.html',
  styleUrls: ['./admin-dashboard.page.scss'],
  standalone: false,
})
export class AdminDashboardPage implements OnInit {
  stats: any = null;
  users: any[] = [];
  isLoading = false;

  constructor(
    private adminService: AdminService,
    private toastController: ToastController,
    private alertController: AlertController
  ) {}

  ngOnInit() {
    this.loadDashboardData();
  }

  doRefresh(event: any) {
    this.loadDashboardData(event);
  }

  loadDashboardData(event?: any) {
    this.isLoading = true;
    
    this.adminService.getStats().subscribe({
      next: (statsData) => {
        this.stats = statsData;
        this.adminService.getUsers().subscribe({
          next: (usersData) => {
            this.users = usersData.users;
            this.isLoading = false;
            if (event) event.target.complete();
          },
          error: () => {
            this.isLoading = false;
            if (event) event.target.complete();
          }
        });
      },
      error: () => {
        this.isLoading = false;
        if (event) event.target.complete();
      }
    });
  }

  async toggleApprove(user: any) {
    const action = user.is_approved ? 'révoquer' : 'approuver';
    const alert = await this.alertController.create({
      header: 'Confirmation',
      message: `Êtes-vous sûr de vouloir ${action} ce freelancer ?`,
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        { 
          text: 'Confirmer', 
          handler: () => {
            this.adminService.toggleApprove(user.id).subscribe({
              next: async (res) => {
                const toast = await this.toastController.create({
                  message: `Statut mis à jour avec succès.`,
                  duration: 2000, color: 'success'
                });
                toast.present();
                user.is_approved = !user.is_approved;
              }
            });
          } 
        }
      ]
    });
    await alert.present();
  }
}
