import { Component, EventEmitter, Input, Output } from '@angular/core';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-portfolio-grid',
  templateUrl: './portfolio-grid.component.html',
  styleUrls: ['./portfolio-grid.component.scss'],
  standalone: false,
})
export class PortfolioGridComponent {
  @Input() projects: any[] = [];
  @Input() editable = false;
  @Output() editProject = new EventEmitter<any>();
  @Output() deleteProject = new EventEmitter<any>();
  @Output() toggleFeatured = new EventEmitter<any>();

  selectedCategory = 'All';
  openedProject: any = null;

  get categories(): string[] {
    const cats = new Set((this.projects || []).map((p) => p.category || 'Other'));
    return ['All', ...Array.from(cats)];
  }

  get visibleProjects(): any[] {
    const sorted = [...(this.projects || [])].sort((a, b) => Number(!!b.is_featured) - Number(!!a.is_featured));
    if (this.selectedCategory === 'All') return sorted;
    return sorted.filter((p) => (p.category || 'Other') === this.selectedCategory);
  }

  openProject(project: any): void {
    this.openedProject = project;
  }

  closeProject(): void {
    this.openedProject = null;
  }

  resolveImage(image: string): string {
    if (!image) return '';
    if (image.startsWith('http://') || image.startsWith('https://')) return image;
    const base = environment.apiUrl.replace('/api', '');
    const normalized = image.replace(/^\/+/, '');
    return `${base}/api/users/uploads/path/${normalized}`;
  }
}

