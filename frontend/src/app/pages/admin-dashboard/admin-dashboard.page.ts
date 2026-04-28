import { Component, OnInit } from '@angular/core';
import { AdminService } from '../../services/admin.service';
import { ToastController, AlertController, ActionSheetController } from '@ionic/angular';

@Component({
  selector: 'app-admin-dashboard',
  templateUrl: './admin-dashboard.page.html',
  styleUrls: ['./admin-dashboard.page.scss'],
  standalone: false,
})
export class AdminDashboardPage implements OnInit {
  currentTab: 'overview' | 'approvals' | 'claims' | 'users' = 'overview';
  
  stats: any = null;
  isLoadingStats = false;
  
  // Approvals state
  approvals: any[] = [];
  approvalCounts: any = { pending: 0, approved: 0, rejected: 0 };
  approvalStatusFilter: string = 'pending';
  approvalsPage = 1;
  approvalsPerPage = 10;
  hasMoreApprovals = true;
  isLoadingApprovals = false;

  // Claims state
  claims: any[] = [];
  claimStatusFilter: string = 'all';
  claimPriorityFilter: string = 'all';
  claimsPage = 1;
  claimsPerPage = 10;
  hasMoreClaims = true;
  isLoadingClaims = false;
  claimStats: any = { open: 0, in_review: 0, resolved: 0, total: 0 };
  
  selectedClaim: any = null;
  isClaimModalOpen = false;
  
  // Users state
  users: any[] = [];
  userSearch = '';
  userRoleFilter = 'all';
  usersPage = 1;
  usersPerPage = 15;
  hasMoreUsers = true;
  isLoadingUsers = false;
  
  isBanModalOpen = false;
  banReason = '';
  banDuration = '24h';
  selectedUserForBan: any = null;
  
  // User Details Modal State
  isUserDetailsModalOpen = false;
  selectedUserDetails: any = null;

  constructor(
    private adminService: AdminService,
    private toastController: ToastController,
    private alertController: AlertController,
    private actionSheetCtrl: ActionSheetController
  ) {}

  ngOnInit() {
    this.loadStats();
    this.loadApprovalCounts();
  }

  doRefresh(event: any) {
    if (this.currentTab === 'overview') {
      this.loadStats(event);
    } else if (this.currentTab === 'approvals') {
      this.loadApprovalCounts();
      this.loadApprovals(true, event);
    } else if (this.currentTab === 'claims') {
      this.loadClaims(true, event);
    } else if (this.currentTab === 'users') {
      this.loadUsers(true, event);
    } else {
      if (event) event.target.complete();
    }
  }

  setTab(tab: 'overview' | 'approvals' | 'claims' | 'users') {
    this.currentTab = tab;
    if (tab === 'approvals' && this.approvals.length === 0) {
      this.loadApprovals(true);
    } else if (tab === 'claims' && this.claims.length === 0) {
      this.loadClaims(true);
    } else if (tab === 'users' && this.users.length === 0) {
      this.loadUsers(true);
    }
  }

  loadStats(event?: any) {
    this.isLoadingStats = true;
    this.adminService.getStats().subscribe({
      next: (data) => {
        this.stats = data;
        this.isLoadingStats = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoadingStats = false;
        if (event) event.target.complete();
      }
    });
  }

  // --- Approvals Logic ---
  loadApprovalCounts() {
    this.adminService.getApprovalCounts().subscribe(counts => this.approvalCounts = counts);
  }

  setApprovalFilter(status: string) {
    this.approvalStatusFilter = status;
    this.loadApprovals(true);
  }

  loadApprovals(reset: boolean = false, event?: any) {
    if (reset) {
      this.approvalsPage = 1;
      this.approvals = [];
      this.hasMoreApprovals = true;
    }
    
    if (!this.hasMoreApprovals) {
      if (event) event.target.complete();
      return;
    }
    
    this.isLoadingApprovals = true;
    this.adminService.getApprovals('', this.approvalStatusFilter, this.approvalsPage, this.approvalsPerPage).subscribe({
      next: (data) => {
        if (reset) {
          this.approvals = data.approvals;
        } else {
          this.approvals = [...this.approvals, ...data.approvals];
        }
        this.hasMoreApprovals = (this.approvalsPage * this.approvalsPerPage) < data.total;
        this.isLoadingApprovals = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoadingApprovals = false;
        if (event) event.target.complete();
      }
    });
  }

  loadMoreApprovals(event: any) {
    this.approvalsPage++;
    this.loadApprovals(false, event);
  }

  async handleApprove(appId: string) {
    this.adminService.updateApproval(appId, 'approved').subscribe({
      next: async (res) => {
        const toast = await this.toastController.create({
          message: 'Demande approuvée avec succès.',
          duration: 2000, color: 'success'
        });
        toast.present();
        this.updateApprovalInList(res.approval);
        this.loadApprovalCounts();
      }
    });
  }

  async handleReject(appId: string) {
    const alert = await this.alertController.create({
      header: 'Rejeter la demande',
      message: 'Veuillez indiquer la raison du rejet:',
      inputs: [
        { name: 'note', type: 'textarea', placeholder: 'Raison (obligatoire)' }
      ],
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        { 
          text: 'Rejeter', 
          role: 'destructive',
          handler: (data) => {
            if (!data.note || data.note.trim() === '') {
              this.toastController.create({ message: 'La raison est obligatoire.', duration: 2000, color: 'danger' }).then(t => t.present());
              return false;
            }
            this.adminService.updateApproval(appId, 'rejected', data.note).subscribe({
              next: async (res) => {
                const toast = await this.toastController.create({
                  message: 'Demande rejetée.',
                  duration: 2000, color: 'medium'
                });
                toast.present();
                this.updateApprovalInList(res.approval);
                this.loadApprovalCounts();
              }
            });
            return true;
          } 
        }
      ]
    });
    await alert.present();
  }
  
  private updateApprovalInList(updatedApp: any) {
    const index = this.approvals.findIndex(a => a._id === updatedApp._id || a.id === updatedApp.id);
    if (index !== -1) {
      if (this.approvalStatusFilter === 'pending') {
        this.approvals.splice(index, 1);
      } else {
        this.approvals[index] = updatedApp;
      }
    }
  }

  // --- Claims Logic ---
  setClaimFilter(filterType: string, val: string) {
    if (filterType === 'status') this.claimStatusFilter = val;
    if (filterType === 'priority') this.claimPriorityFilter = val;
    this.loadClaims(true);
  }

  loadClaims(reset: boolean = false, event?: any) {
    if (reset) {
      this.claimsPage = 1;
      this.claims = [];
      this.hasMoreClaims = true;
    }
    if (!this.hasMoreClaims) {
      if (event) event.target.complete();
      return;
    }
    
    this.isLoadingClaims = true;
    this.adminService.getClaims(this.claimStatusFilter, this.claimPriorityFilter, 'all', this.claimsPage, this.claimsPerPage).subscribe({
      next: (data) => {
        if (reset) {
          this.claims = data.claims;
        } else {
          this.claims = [...this.claims, ...data.claims];
        }
        this.hasMoreClaims = (this.claimsPage * this.claimsPerPage) < data.total;
        
        // Calculate basic local stats or fetch from backend ideally
        this.claimStats = {
          open: this.claims.filter(c => c.status === 'open').length,
          in_review: this.claims.filter(c => c.status === 'in_review').length,
          resolved: this.claims.filter(c => c.status === 'resolved').length,
          total: data.total
        };

        this.isLoadingClaims = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoadingClaims = false;
        if (event) event.target.complete();
      }
    });
  }

  loadMoreClaims(event: any) {
    this.claimsPage++;
    this.loadClaims(false, event);
  }
  
  openClaimModal(claim: any) {
    this.selectedClaim = { ...claim };
    this.isClaimModalOpen = true;
  }
  
  closeClaimModal() {
    this.isClaimModalOpen = false;
    this.selectedClaim = null;
  }
  
  saveClaim() {
    if (!this.selectedClaim) return;
    this.adminService.updateClaim(this.selectedClaim.id || this.selectedClaim._id, this.selectedClaim.status, this.selectedClaim.admin_note, this.selectedClaim.priority).subscribe({
      next: async (res) => {
        const toast = await this.toastController.create({ message: 'Réclamation mise à jour', duration: 2000, color: 'success' });
        toast.present();
        const idx = this.claims.findIndex(c => (c.id || c._id) === (res.claim.id || res.claim._id));
        if (idx !== -1) {
          this.claims[idx] = res.claim;
        }
        this.closeClaimModal();
      }
    });
  }

  // --- Users Logic ---
  onUserSearchChange(event: any) {
    this.userSearch = event.detail.value;
    this.loadUsers(true);
  }

  setUserRoleFilter(role: string) {
    this.userRoleFilter = role;
    this.loadUsers(true);
  }

  loadUsers(reset: boolean = false, event?: any) {
    if (reset) {
      this.usersPage = 1;
      this.users = [];
      this.hasMoreUsers = true;
    }
    if (!this.hasMoreUsers) {
      if (event) event.target.complete();
      return;
    }
    
    this.isLoadingUsers = true;
    this.adminService.getUsers(this.userRoleFilter, '', this.userSearch, this.usersPage, this.usersPerPage).subscribe({
      next: (data) => {
        if (reset) {
          this.users = data.users;
        } else {
          this.users = [...this.users, ...data.users];
        }
        this.hasMoreUsers = (this.usersPage * this.usersPerPage) < data.total;
        this.isLoadingUsers = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoadingUsers = false;
        if (event) event.target.complete();
      }
    });
  }

  loadMoreUsers(event: any) {
    this.usersPage++;
    this.loadUsers(false, event);
  }

  async openUserActionSheet(user: any) {
    const buttons = [];
    
    buttons.push({
      text: 'Voir le profil complet',
      icon: 'person',
      handler: () => {
        this.openUserDetails(user);
      }
    });

    if (user.role === 'freelancer' && !user.is_approved) {
      buttons.push({
        text: 'Approuver le compte',
        icon: 'checkmark-circle',
        handler: () => {
          this.adminService.toggleApprove(user.id || user._id).subscribe(async res => {
            const toast = await this.toastController.create({ message: 'Compte approuvé', duration: 2000, color: 'success' });
            toast.present();
            user.is_approved = true;
          });
        }
      });
    }

    if (user.status === 'banned') {
      buttons.push({
        text: 'Débannir l\'utilisateur',
        icon: 'refresh-circle',
        handler: () => {
          this.adminService.unbanUser(user.id || user._id).subscribe(async res => {
            const toast = await this.toastController.create({ message: 'Utilisateur débanni', duration: 2000, color: 'success' });
            toast.present();
            user.status = 'active';
            if (this.selectedUserDetails && (this.selectedUserDetails.user.id || this.selectedUserDetails.user._id) === (user.id || user._id)) {
              this.selectedUserDetails.user.status = 'active';
            }
          });
        }
      });
    } else {
      buttons.push({
        text: 'Bannir temporairement',
        icon: 'warning',
        handler: () => {
          this.openBanModal(user);
        }
      });
      buttons.push({
        text: 'Bannir définitivement',
        icon: 'ban',
        role: 'destructive',
        handler: () => {
          this.openPermanentBanAlert(user);
        }
      });
    }

    buttons.push({
      text: 'Supprimer le compte',
      icon: 'trash',
      role: 'destructive',
      handler: () => {
        this.openDeleteAlert(user);
      }
    });

    buttons.push({
      text: 'Annuler',
      icon: 'close',
      role: 'cancel'
    });

    const actionSheet = await this.actionSheetCtrl.create({
      header: `Options pour ${user.full_name}`,
      buttons: buttons
    });
    await actionSheet.present();
  }

  openBanModal(user: any) {
    this.selectedUserForBan = user;
    this.banReason = '';
    this.banDuration = '24h';
    this.isBanModalOpen = true;
  }
  
  closeBanModal() {
    this.isBanModalOpen = false;
    this.selectedUserForBan = null;
  }
  
  async submitBan() {
    if (this.banReason.length < 20) {
      const toast = await this.toastController.create({ message: 'Raison doit contenir au moins 20 caractères', duration: 2000, color: 'danger' });
      return toast.present();
    }
    
    let expiresAt: string | null = null;
    const now = new Date();
    if (this.banDuration === '24h') {
      now.setHours(now.getHours() + 24);
      expiresAt = now.toISOString();
    } else if (this.banDuration === '3j') {
      now.setDate(now.getDate() + 3);
      expiresAt = now.toISOString();
    } else if (this.banDuration === '7j') {
      now.setDate(now.getDate() + 7);
      expiresAt = now.toISOString();
    } else if (this.banDuration === '30j') {
      now.setDate(now.getDate() + 30);
      expiresAt = now.toISOString();
    }
    
    this.adminService.banUser(this.selectedUserForBan.id || this.selectedUserForBan._id, this.banReason, expiresAt).subscribe(async res => {
      const toast = await this.toastController.create({ message: 'Utilisateur banni', duration: 2000, color: 'danger' });
      toast.present();
      this.selectedUserForBan.status = 'banned';
      if (this.selectedUserDetails && (this.selectedUserDetails.user.id || this.selectedUserDetails.user._id) === (this.selectedUserForBan.id || this.selectedUserForBan._id)) {
         this.selectedUserDetails.user.status = 'banned';
      }
      this.closeBanModal();
    });
  }

  async openPermanentBanAlert(user: any) {
    const alert = await this.alertController.create({
      header: 'Bannir définitivement',
      message: 'Veuillez indiquer la raison:',
      inputs: [{ name: 'note', type: 'textarea', placeholder: 'Raison (obligatoire, min 20 chars)' }],
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        { 
          text: 'Bannir', role: 'destructive',
          handler: (data) => {
            if (!data.note || data.note.length < 20) {
               this.toastController.create({ message: 'Raison obligatoire (min 20 caractères)', duration: 2000, color: 'danger' }).then(t => t.present());
               return false;
            }
            this.adminService.banUser(user.id || user._id, data.note, null).subscribe(async res => {
               user.status = 'banned';
               if (this.selectedUserDetails && (this.selectedUserDetails.user.id || this.selectedUserDetails.user._id) === (user.id || user._id)) {
                 this.selectedUserDetails.user.status = 'banned';
               }
               const toast = await this.toastController.create({ message: 'Bannissement définitif appliqué', duration: 2000, color: 'danger' });
               toast.present();
            });
            return true;
          }
        }
      ]
    });
    await alert.present();
  }

  async openDeleteAlert(user: any) {
    const alert = await this.alertController.create({
      header: 'Supprimer le compte',
      message: 'Êtes-vous sûr ? Cette action est irréversible et annulera ses projets actifs.',
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        { 
          text: 'Supprimer', role: 'destructive',
          handler: () => {
            this.adminService.deleteUser(user.id || user._id).subscribe(async res => {
               user.status = 'deleted';
               if (this.selectedUserDetails && (this.selectedUserDetails.user.id || this.selectedUserDetails.user._id) === (user.id || user._id)) {
                 this.selectedUserDetails.user.status = 'deleted';
               }
               const toast = await this.toastController.create({ message: 'Compte supprimé avec succès', duration: 2000, color: 'dark' });
               toast.present();
            });
          }
        }
      ]
    });
    await alert.present();
  }

  openUserDetails(user: any) {
    this.adminService.getUserDetails(user.id || user._id).subscribe(res => {
      this.selectedUserDetails = res;
      this.isUserDetailsModalOpen = true;
    });
  }

  closeUserDetails() {
    this.isUserDetailsModalOpen = false;
    this.selectedUserDetails = null;
  }

  getMathMax(a: number, b: number): number {
    return Math.max(a, b);
  }
}
