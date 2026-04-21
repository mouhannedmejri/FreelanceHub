import { Component, OnInit } from '@angular/core';
import { AlertController, ToastController } from '@ionic/angular';
import { AuthService } from '../../services/auth.service';
import { ProfileService } from '../../services/profile.service';
import { FullProfile } from '../../models/profile.model';
import { User } from '../../models/user.model';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.page.html',
  styleUrls: ['./profile.page.scss'],
  standalone: false,
})
export class ProfilePage implements OnInit {
  profile: FullProfile | null = null;
  user: User | null = null;
  isLoading = true;

  constructor(
    private authService: AuthService,
    private profileService: ProfileService,
    private alertController: AlertController,
    private toastController: ToastController
  ) {}

  ngOnInit() {
    this.user = this.authService.currentUser;
    if (this.user) {
      this.loadProfile();
    }
  }

  ionViewWillEnter() {
    this.user = this.authService.currentUser;
    if (this.user && !this.profile) {
      this.loadProfile();
    }
  }

  loadProfile() {
    if (!this.user) return;
    this.isLoading = true;
    this.profileService.fetchProfile(this.user.id, true).subscribe({
      next: (data) => {
        this.profile = data;
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
      },
    });
  }

  getInitials(): string {
    const name =
      this.profile?.user?.full_name || this.user?.full_name || '';
    return name
      .split(' ')
      .map((n: string) => n[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  }

  async editProfile() {
    const p = this.profile?.profile;
    const alert = await this.alertController.create({
      header: 'Modifier le profil',
      cssClass: 'edit-profile-alert',
      inputs: [
        {
          name: 'title',
          type: 'text',
          placeholder: 'Titre professionnel',
          value: p?.title || '',
        },
        {
          name: 'bio',
          type: 'textarea',
          placeholder: 'Bio',
          value: p?.bio || '',
        },
        {
          name: 'hourly_rate',
          type: 'number',
          placeholder: 'Tarif horaire (€)',
          value: p?.hourly_rate?.toString() || '',
        },
        {
          name: 'location',
          type: 'text',
          placeholder: 'Localisation',
          value: p?.location || '',
        },
        {
          name: 'phone',
          type: 'tel',
          placeholder: 'Téléphone',
          value: p?.phone || '',
        },
      ],
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        {
          text: 'Sauvegarder',
          handler: (data) => {
            this.profileService
              .updateProfile({
                title: data.title,
                bio: data.bio,
                hourly_rate: parseFloat(data.hourly_rate) || 0,
                location: data.location,
                phone: data.phone,
              })
              .subscribe({
                next: (updated) => {
                  this.profile = updated;
                  this.showToast('Profil mis à jour avec succès');
                },
                error: () => {
                  this.showToast('Erreur lors de la mise à jour');
                },
              });
          },
        },
      ],
    });
    await alert.present();
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];

    if (file.size > 5 * 1024 * 1024) {
      this.showToast('Le fichier dépasse la taille maximale de 5 MB');
      return;
    }
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      this.showToast('Seuls les fichiers PDF sont acceptés');
      return;
    }

    this.profileService.uploadCV(file).subscribe({
      next: (updated) => {
        this.profile = updated;
        this.showToast('CV téléchargé avec succès');
      },
      error: () => {
        this.showToast('Erreur lors du téléchargement');
      },
    });

    // Reset input so selecting the same file again triggers change
    input.value = '';
  }

  private async showToast(message: string) {
    const toast = await this.toastController.create({
      message,
      duration: 2500,
      position: 'bottom',
      color: 'dark',
    });
    await toast.present();
  }
}
