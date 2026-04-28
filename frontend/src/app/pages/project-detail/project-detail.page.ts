import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ToastController, AlertController } from '@ionic/angular';
import { ProjectService } from '../../services/project.service';
import { AuthService } from '../../services/auth.service';
import {
  ProjectDetail,
  Milestone,
  Task,
  Deliverable
} from '../../models/project.model';

@Component({
  selector: 'app-project-detail',
  templateUrl: './project-detail.page.html',
  styleUrls: ['./project-detail.page.scss'],
  standalone: false,
})
export class ProjectDetailPage implements OnInit {
  projectId = '';
  project: ProjectDetail | null = null;
  isLoading = true;
  currentTab: 'milestones' | 'tasks' | 'deliverables' | 'overview' = 'milestones';

  // Kanban columns
  kanbanColumns: { key: string; label: string; tasks: Task[] }[] = [];

  // Drag state
  draggedTask: Task | null = null;

  // Expanded milestones
  expandedMilestones: Set<string> = new Set();

  constructor(
    private route: ActivatedRoute,
    private projectService: ProjectService,
    private authService: AuthService,
    private toastController: ToastController,
    private alertController: AlertController
  ) {}

  ngOnInit() {
    this.projectId = this.route.snapshot.paramMap.get('id') || '';
    this.loadProject();
  }

  loadProject(event?: any) {
    this.isLoading = true;
    this.projectService.getProjectDetail(this.projectId).subscribe({
      next: (data) => {
        this.project = data.project;
        this.buildKanban();
        this.isLoading = false;
        if (event) event.target.complete();
      },
      error: () => {
        this.isLoading = false;
        if (event) event.target.complete();
        this.showToast('Erreur de chargement du projet', 'danger');
      }
    });
  }

  doRefresh(event: any) {
    this.loadProject(event);
  }

  setTab(tab: 'milestones' | 'tasks' | 'deliverables' | 'overview') {
    this.currentTab = tab;
  }

  // ── COMPUTED VALUES ───────────────────────────
  get milestonesDone(): number {
    return (this.project?.milestones || []).filter(m => m.status === 'done').length;
  }

  get milestonesTotal(): number {
    return (this.project?.milestones || []).length;
  }

  get progressPercent(): number {
    return this.project?.progress_percent || 0;
  }

  get totalBudget(): number {
    return this.project?.total_budget || this.project?.budget || 0;
  }

  get paidAmount(): number {
    return this.project?.paid_amount || 0;
  }

  get remainingBudget(): number {
    return this.totalBudget - this.paidAmount;
  }

  get progressDashOffset(): number {
    const circumference = 2 * Math.PI * 54;
    return circumference - (this.progressPercent / 100) * circumference;
  }

  get progressCircumference(): number {
    return 2 * Math.PI * 54;
  }

  // ── MILESTONES ────────────────────────────────
  toggleMilestone(mid: string) {
    if (this.expandedMilestones.has(mid)) {
      this.expandedMilestones.delete(mid);
    } else {
      this.expandedMilestones.add(mid);
    }
  }

  isMilestoneExpanded(mid: string): boolean {
    return this.expandedMilestones.has(mid);
  }

  getTasksForMilestone(mid: string): Task[] {
    return (this.project?.tasks || []).filter(t => t.milestone_id === mid);
  }

  getMilestoneStatusColor(status: string): string {
    switch (status) {
      case 'done': return '#10b981';
      case 'in_progress': return '#f59e0b';
      default: return '#6b7280';
    }
  }

  getMilestoneStatusLabel(status: string): string {
    switch (status) {
      case 'done': return 'Terminé';
      case 'in_progress': return 'En cours';
      default: return 'En attente';
    }
  }

  async addMilestone() {
    const alert = await this.alertController.create({
      header: 'Nouveau Milestone',
      cssClass: 'dark-alert',
      inputs: [
        { name: 'title', type: 'text', placeholder: 'Titre du milestone' },
        { name: 'due_date', type: 'date', placeholder: 'Date limite' },
        { name: 'budget_allocated', type: 'number', placeholder: 'Budget alloué (€)' }
      ],
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        {
          text: 'Créer',
          handler: (data) => {
            if (!data.title) return;
            this.projectService.createMilestone(this.projectId, {
              title: data.title,
              due_date: data.due_date || undefined,
              budget_allocated: parseFloat(data.budget_allocated) || 0
            }).subscribe({
              next: (res) => {
                this.project?.milestones.push(res.milestone);
                this.showToast('Milestone créé !', 'success');
              },
              error: () => this.showToast('Erreur lors de la création', 'danger')
            });
          }
        }
      ]
    });
    await alert.present();
  }

  updateMilestoneStatus(mid: string, newStatus: string) {
    this.projectService.updateMilestone(this.projectId, mid, { status: newStatus as any }).subscribe({
      next: (res) => {
        const m = this.project?.milestones.find(x => x.id === mid);
        if (m) m.status = res.milestone.status;
        this.showToast('Milestone mis à jour', 'success');
      },
      error: () => this.showToast('Erreur', 'danger')
    });
  }

  // ── TASKS / KANBAN ────────────────────────────
  buildKanban() {
    const tasks = this.project?.tasks || [];
    this.kanbanColumns = [
      { key: 'todo', label: 'À faire', tasks: tasks.filter(t => t.status === 'todo') },
      { key: 'in_progress', label: 'En cours', tasks: tasks.filter(t => t.status === 'in_progress') },
      { key: 'review', label: 'Revue', tasks: tasks.filter(t => t.status === 'review') },
      { key: 'done', label: 'Terminé', tasks: tasks.filter(t => t.status === 'done') }
    ];
  }

  getPriorityColor(priority: string): string {
    switch (priority) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  }

  getPriorityLabel(priority: string): string {
    switch (priority) {
      case 'high': return 'Haute';
      case 'medium': return 'Moyenne';
      case 'low': return 'Basse';
      default: return priority;
    }
  }

  onDragStart(task: Task) {
    this.draggedTask = task;
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
  }

  onDrop(event: DragEvent, targetStatus: string) {
    event.preventDefault();
    if (!this.draggedTask || this.draggedTask.status === targetStatus) {
      this.draggedTask = null;
      return;
    }
    this.moveTask(this.draggedTask, targetStatus);
    this.draggedTask = null;
  }

  moveTask(task: Task, newStatus: string) {
    this.projectService.updateTask(this.projectId, task.id, { status: newStatus as any }).subscribe({
      next: (res) => {
        task.status = res.task.status;
        if (this.project) {
          this.project.progress_percent = res.progress_percent;
        }
        this.buildKanban();
        this.showToast('Tâche déplacée', 'success');
      },
      error: () => this.showToast('Erreur', 'danger')
    });
  }

  async addTask() {
    const milestoneOptions = (this.project?.milestones || []).map(m => ({
      name: 'milestone_id',
      type: 'radio' as const,
      label: m.title,
      value: m.id
    }));

    // Step 1: pick milestone (optional)
    let selectedMilestone = '';
    if (milestoneOptions.length > 0) {
      const milestoneAlert = await this.alertController.create({
        header: 'Associer à un milestone ?',
        cssClass: 'dark-alert',
        inputs: [
          { name: 'milestone_id', type: 'radio', label: 'Aucun', value: '', checked: true },
          ...milestoneOptions
        ],
        buttons: [
          { text: 'Annuler', role: 'cancel' },
          { text: 'Suivant', handler: (data) => { selectedMilestone = data; } }
        ]
      });
      await milestoneAlert.present();
      await milestoneAlert.onDidDismiss();
    }

    const alert = await this.alertController.create({
      header: 'Nouvelle Tâche',
      cssClass: 'dark-alert',
      inputs: [
        { name: 'title', type: 'text', placeholder: 'Titre de la tâche' },
        { name: 'description', type: 'textarea', placeholder: 'Description' },
        { name: 'due_date', type: 'date', placeholder: 'Date limite' }
      ],
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        {
          text: 'Créer',
          handler: (data) => {
            if (!data.title) return;
            this.projectService.createTask(this.projectId, {
              title: data.title,
              description: data.description || '',
              milestone_id: selectedMilestone || undefined,
              due_date: data.due_date || undefined
            }).subscribe({
              next: (res) => {
                this.project?.tasks.push(res.task);
                if (this.project) {
                  this.project.progress_percent = res.progress_percent;
                }
                this.buildKanban();
                this.showToast('Tâche créée !', 'success');
              },
              error: () => this.showToast('Erreur', 'danger')
            });
          }
        }
      ]
    });
    await alert.present();
  }

  async deleteTask(task: Task) {
    const alert = await this.alertController.create({
      header: 'Supprimer la tâche ?',
      message: `Êtes-vous sûr de vouloir supprimer "${task.title}" ?`,
      cssClass: 'dark-alert',
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        {
          text: 'Supprimer',
          role: 'destructive',
          handler: () => {
            this.projectService.deleteTask(this.projectId, task.id).subscribe({
              next: (res) => {
                if (this.project) {
                  this.project.tasks = this.project.tasks.filter(t => t.id !== task.id);
                  this.project.progress_percent = res.progress_percent;
                }
                this.buildKanban();
                this.showToast('Tâche supprimée', 'success');
              },
              error: () => this.showToast('Erreur', 'danger')
            });
          }
        }
      ]
    });
    await alert.present();
  }

  // ── DELIVERABLES ──────────────────────────────
  async addDeliverable() {
    const alert = await this.alertController.create({
      header: 'Ajouter un livrable',
      cssClass: 'dark-alert',
      inputs: [
        { name: 'file_name', type: 'text', placeholder: 'Nom du fichier' },
        { name: 'file_url', type: 'url', placeholder: 'URL du fichier' }
      ],
      buttons: [
        { text: 'Annuler', role: 'cancel' },
        {
          text: 'Ajouter',
          handler: (data) => {
            if (!data.file_url) return;
            this.projectService.addDeliverable(this.projectId, {
              file_url: data.file_url,
              file_name: data.file_name || undefined
            }).subscribe({
              next: (res) => {
                this.project?.deliverables_list.push(res.deliverable);
                this.showToast('Livrable ajouté !', 'success');
              },
              error: () => this.showToast('Erreur', 'danger')
            });
          }
        }
      ]
    });
    await alert.present();
  }

  confirmDeliverable(d: Deliverable) {
    this.projectService.confirmDeliverable(this.projectId, d.id).subscribe({
      next: () => {
        d.confirmed = true;
        this.showToast('Livrable confirmé', 'success');
      },
      error: () => this.showToast('Erreur', 'danger')
    });
  }

  get isClient(): boolean {
    return this.project?.client_id === this.authService.currentUser?.id;
  }

  // ── ACTIVITY FEED ─────────────────────────────
  get activityFeed(): { desc: string; date: string; icon: string; color: string }[] {
    if (!this.project) return [];
    const items: { desc: string; date: string; icon: string; color: string }[] = [];

    for (const t of this.project.tasks) {
      if (t.status === 'done') {
        items.push({
          desc: `Tâche "${t.title}" terminée`,
          date: t.created_at,
          icon: 'checkmark-circle',
          color: '#10b981'
        });
      } else if (t.status === 'in_progress') {
        items.push({
          desc: `Tâche "${t.title}" en cours`,
          date: t.created_at,
          icon: 'play-circle',
          color: '#3b82f6'
        });
      } else if (t.status === 'review') {
        items.push({
          desc: `Tâche "${t.title}" en revue`,
          date: t.created_at,
          icon: 'eye',
          color: '#f59e0b'
        });
      }
    }

    for (const m of this.project.milestones) {
      if (m.status === 'done') {
        items.push({
          desc: `Milestone "${m.title}" terminé`,
          date: m.due_date,
          icon: 'flag',
          color: '#10b981'
        });
      }
    }

    items.sort((a, b) => (b.date || '').localeCompare(a.date || ''));
    return items.slice(0, 15);
  }

  // ── HELPERS ──────────────────────────────────
  private async showToast(message: string, color: string = 'primary') {
    const toast = await this.toastController.create({ message, duration: 2000, color, position: 'bottom' });
    await toast.present();
  }
}
