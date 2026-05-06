import { Component, OnDestroy, OnInit } from '@angular/core';
import { AlertController, ToastController, ModalController } from '@ionic/angular';
import { AuthService } from '../../services/auth.service';
import { ProfileService } from '../../services/profile.service';
import { FullProfile } from '../../models/profile.model';
import { User } from '../../models/user.model';
import { ReviewService } from '../../services/review.service';
import { Review } from '../../models/review.model';
import { LeaveReviewComponent } from '../../components/leave-review/leave-review.component';
import { ActivatedRoute, Router } from '@angular/router';
import { GuestAccessService } from '../../services/guest-access.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { ConversationService } from '../../services/conversation.service';
import { PortfolioService } from '../../services/portfolio.service';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.page.html',
  styleUrls: ['./profile.page.scss'],
  standalone: false,
})
export class ProfilePage implements OnInit, OnDestroy {
  profile: FullProfile | null = null;
  user: User | null = null;
  isLoading = true;
  reviews: Review[] = [];

  currentTab: 'projects' | 'about' | 'reviews' = 'about';
  bioExpanded = false;
  isFollowing = false;
  followerCount = 0;
  isFavorite = false;
  editableInterests: string[] = [];

  portfolioModalOpen = false;
  editingProject: any = null;

  private destroy$ = new Subject<void>();

  constructor(
    private authService: AuthService,
    private profileService: ProfileService,
    private reviewService: ReviewService,
    private conversationService: ConversationService,
    private portfolioService: PortfolioService,
    private route: ActivatedRoute,
    private router: Router,
    private guestAccessService: GuestAccessService,
    private alertController: AlertController,
    private toastController: ToastController,
    private modalController: ModalController
  ) {}

  ngOnInit() {
    this.user = this.authService.currentUser;
    this.route.queryParamMap.pipe(takeUntil(this.destroy$)).subscribe(() => {
      // Ensure user is loaded before loading profile
      if (!this.user) {
        this.user = this.authService.currentUser;
      }
      this.loadProfile();
    });
  }

  ionViewWillEnter() {
    this.user = this.authService.currentUser;
    // Reload profile when returning to the page
    this.loadProfile();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadProfile() {
    const fromQuery = this.route.snapshot.queryParamMap.get('userId');
    const username = this.route.snapshot.paramMap.get('username') || this.route.parent?.snapshot.paramMap.get('username');
    const safeQueryUserId = fromQuery && /^[a-fA-F0-9]{24}$/.test(fromQuery) ? fromQuery : null;
    const targetUserId = safeQueryUserId || this.user?.id;

    this.isLoading = true;
    const request$ = username
      ? this.profileService.fetchProfileByUsername(username)
      : targetUserId
      ? this.profileService.fetchProfile(targetUserId as any, true)
      : null;

    if (!request$) {
      this.isLoading = false;
      return;
    }

    request$.subscribe({
      next: (data) => {
        this.profile = data;
        this.editableInterests = Array.isArray(data.user?.interests) ? [...data.user.interests] : [];
        this.isFollowing = data.is_following || false;
        this.followerCount = data.follower_count || 0;
        this.syncFavoriteState();
        this.isLoading = false;
        this.loadReviews(data.user.id as any);
      },
      error: () => {
        this.isLoading = false;
      },
    });
  }

  loadReviews(userId: number) {
    this.reviewService.getUserReviews(userId).subscribe({ next: (res) => (this.reviews = res.reviews) });
  }

  setTab(tab: 'projects' | 'about' | 'reviews') {
    this.currentTab = tab;
  }

  toggleFollow() {
    if (this.authService.isGuest) {
      this.guestAccessService.showSignupPrompt('Sign up to follow freelancers.');
      return;
    }
    if (!this.profile?.user) return;
    if (String(this.profile.user.id) === String(this.user?.id)) {
      this.showToast('You cannot follow your own profile');
      return;
    }

    this.profileService.toggleFollow(this.profile.user.id).subscribe({
      next: (res) => {
        this.isFollowing = res.action === 'followed';
        this.followerCount = res.follower_count;
        this.showToast(this.isFollowing ? 'Vous suivez ce freelancer' : 'Vous ne suivez plus ce freelancer');
      },
      error: () => this.showToast('Erreur'),
    });
  }

  contactFreelancer() {
    if (this.authService.isGuest) {
      this.guestAccessService.showSignupPrompt('Sign up to contact freelancers.');
      return;
    }
    if (!this.profile?.user?.id) return;
    if (String(this.profile.user.id) === String(this.user?.id)) {
      this.showToast('You cannot message yourself');
      return;
    }
    if (!/^[a-fA-F0-9]{24}$/.test(String(this.profile.user.id))) {
      this.showToast('Invalid target profile');
      return;
    }

    this.conversationService.startConversation({ user_id: this.profile.user.id }).subscribe({
      next: (res) => this.router.navigate(['/home/messages'], { queryParams: { conversationId: res.conversation.id } }),
      error: (err) => this.showToast(err?.error?.error || 'Unable to start conversation'),
    });
  }

  toggleFavorite() {
    if (!this.profile?.user?.id) return;
    const profileId = String(this.profile.user.id);
    const raw = localStorage.getItem('favoriteFreelancers');
    const favorites: string[] = raw ? JSON.parse(raw) : [];

    if (favorites.includes(profileId)) {
      localStorage.setItem('favoriteFreelancers', JSON.stringify(favorites.filter((id) => id !== profileId)));
      this.isFavorite = false;
      this.showToast('Removed from favorites');
      return;
    }

    favorites.push(profileId);
    localStorage.setItem('favoriteFreelancers', JSON.stringify(favorites));
    this.isFavorite = true;
    this.showToast('Added to favorites');
  }

  saveInterests() {
    if (!this.isOwnProfile) {
      this.showToast('You can only edit your own interests');
      return;
    }
    this.profileService.updateInterests(this.editableInterests).subscribe({
      next: async (res) => {
        if (this.profile) this.profile.user = { ...this.profile.user, interests: res.user.interests || [] } as any;
        await this.authService.setCurrentUser(res.user);
        this.showToast('Interests updated');
      },
      error: () => this.showToast('Unable to update interests'),
    });
  }

  openAddProjectModal() {
    this.editingProject = null;
    this.portfolioModalOpen = true;
  }

  openEditProjectModal(project: any) {
    this.editingProject = project;
    this.portfolioModalOpen = true;
  }

  onProjectModalDismiss() {
    this.portfolioModalOpen = false;
    this.editingProject = null;
  }

  savePortfolioProject(evt: { payload: any; images: File[] }) {
    const request$ = this.editingProject?.id
      ? this.portfolioService.updateProject(this.editingProject.id, evt.payload)
      : this.portfolioService.addProject(evt.payload);

    request$.subscribe({
      next: (res) => {
        const projectId = String(res?.project?.id || this.editingProject?.id || '');
        if (evt.images?.length && projectId) {
          this.portfolioService.uploadProjectImages(projectId, evt.images).subscribe({
            next: () => this.finalizeProjectSave(),
            error: () => this.finalizeProjectSave(),
          });
        } else {
          this.finalizeProjectSave();
        }
      },
      error: () => this.showToast('Unable to save project'),
    });
  }

  private finalizeProjectSave() {
    this.showToast('Project saved');
    this.onProjectModalDismiss();
    this.loadProfile();
  }

  deletePortfolioProject(project: any) {
    if (!project?.id) return;
    this.portfolioService.deleteProject(String(project.id)).subscribe({
      next: () => {
        this.showToast('Project deleted');
        this.loadProfile();
      },
      error: () => this.showToast('Unable to delete project'),
    });
  }

  toggleFeaturedProject(project: any) {
    if (!project?.id) return;
    this.portfolioService.toggleFeatured(String(project.id)).subscribe({
      next: () => this.loadProfile(),
      error: () => this.showToast('Unable to update featured status'),
    });
  }

  async shareProfile() {
    const url = this.profile?.user?.username ? `${window.location.origin}/freelancer/${this.profile.user.username}` : window.location.href;
    await navigator.clipboard.writeText(url);
    this.showToast('Profile link copied');
  }

  toggleBio() {
    this.bioExpanded = !this.bioExpanded;
  }

  getInitials(): string {
    const name = this.profile?.user?.full_name || this.user?.full_name || '';
    return name.split(' ').map((n: string) => n[0]).join('').substring(0, 2).toUpperCase();
  }

  get earningsFormatted(): string {
    const e = this.profile?.stats?.earnings || 0;
    if (e >= 1000) return `$${Math.round(e / 1000)}K+`;
    return `$${e}`;
  }

  get hourlyRate(): number {
    return this.profile?.profile?.hourly_rate || 0;
  }

  get availabilityColor(): string {
    const a = this.profile?.availability || '';
    if (a === 'Online now') return '#10b981';
    if (a.includes('2h')) return '#f59e0b';
    if (a.includes('today')) return '#3b82f6';
    return '#6b7280';
  }

  get availabilityLabel(): string {
    const status = this.profile?.profile?.availability_status || 'available';
    if (status === 'busy') return 'Busy';
    if (status === 'unavailable') return 'Unavailable';
    return 'Available';
  }

  async leaveReview() {
    if (this.authService.isGuest) {
      this.guestAccessService.showSignupPrompt('Sign up to leave a review.');
      return;
    }
    if (!this.profile?.user) return;
    const modal = await this.modalController.create({ component: LeaveReviewComponent, componentProps: { targetUserId: this.profile.user.id } });
    await modal.present();
    const { data, role } = await modal.onDidDismiss();
    if (role === 'confirm' && data) {
      this.reviewService.submitReview({ target_user_id: this.profile.user.id, rating: data.rating, comment: data.comment }).subscribe({
        next: () => {
          this.showToast('Avis publié avec succès');
          this.loadReviews(this.profile!.user.id);
        },
        error: (err) => this.showToast(err.error?.error || 'Erreur lors de la publication'),
      });
    }
  }

  async editProfile() {
    if (!this.isOwnProfile) {
      this.showToast('You can only edit your own profile');
      return;
    }
    const p = this.profile?.profile;
    const alert = await this.alertController.create({
      header: 'Modifier le profil',
      cssClass: 'edit-profile-alert',
      inputs: [
        { name: 'title', type: 'text', placeholder: 'Titre professionnel', value: p?.title || '' },
        { name: 'bio', type: 'textarea', placeholder: 'Bio', value: p?.bio || '' },
        { name: 'hourly_rate', type: 'number', placeholder: 'Tarif horaire (€)', value: p?.hourly_rate?.toString() || '' },
        { name: 'location', type: 'text', placeholder: 'Localisation', value: p?.location || '' },
        { name: 'phone', type: 'tel', placeholder: 'Téléphone', value: p?.phone || '' },
        { name: 'video_intro_url', type: 'url', placeholder: 'Video intro URL', value: p?.video_intro_url || '' },
      ],
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        {
          text: 'Sauvegarder',
          handler: (data) => {
            this.profileService.updateProfile({
              title: data.title,
              bio: data.bio,
              hourly_rate: parseFloat(data.hourly_rate) || 0,
              location: data.location,
              phone: data.phone,
              video_intro_url: data.video_intro_url,
            }).subscribe({
              next: (updated) => {
                this.profile = updated;
                this.showToast('Profil mis à jour avec succès');
              },
              error: () => this.showToast('Erreur lors de la mise à jour'),
            });
          },
        },
      ],
    });
    await alert.present();
  }

  onFileSelected(event: Event) {
    if (!this.isOwnProfile) return;
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
      error: () => this.showToast('Erreur lors du téléchargement'),
    });
    input.value = '';
  }

  private async showToast(message: string) {
    const toast = await this.toastController.create({ message, duration: 2500, position: 'bottom', color: 'dark' });
    await toast.present();
  }

  formatBytes(bytes?: number, decimals = 2) {
    if (!bytes || !+bytes) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
  }

  get isOwnProfile(): boolean {
    return !!this.user && !!this.profile && String(this.user.id) === String(this.profile.user.id);
  }

  get isGuest(): boolean {
    return this.authService.isGuest;
  }

  private syncFavoriteState() {
    const profileId = this.profile?.user?.id ? String(this.profile.user.id) : '';
    if (!profileId) {
      this.isFavorite = false;
      return;
    }
    const raw = localStorage.getItem('favoriteFreelancers');
    const favorites: string[] = raw ? JSON.parse(raw) : [];
    this.isFavorite = favorites.includes(profileId);
  }
}

