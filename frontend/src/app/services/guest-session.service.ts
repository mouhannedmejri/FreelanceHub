import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface IntendedAction {
  type: string;        // e.g., 'apply_to_offer', 'create_offer', 'send_message', 'leave_review'
  targetId?: string;   // e.g., offer_id, user_id
  route?: string;      // route to navigate to after login
  data?: any;          // additional context
  timestamp: number;
}

const INTENDED_ACTION_KEY = 'freelancehub_intended_action';

@Injectable({ providedIn: 'root' })
export class GuestSessionService {
  private intendedAction$ = new BehaviorSubject<IntendedAction | null>(this.loadIntendedAction());

  get currentIntendedAction(): IntendedAction | null {
    return this.intendedAction$.value;
  }

  /** Store an intended action that the guest wanted to perform */
  setIntendedAction(action: IntendedAction): void {
    localStorage.setItem(INTENDED_ACTION_KEY, JSON.stringify(action));
    this.intendedAction$.next(action);
  }

  /** Retrieve and clear the intended action (called after login) */
  consumeIntendedAction(): IntendedAction | null {
    const action = this.loadIntendedAction();
    this.clearIntendedAction();
    return action;
  }

  /** Clear any stored intended action */
  clearIntendedAction(): void {
    localStorage.removeItem(INTENDED_ACTION_KEY);
    this.intendedAction$.next(null);
  }

  /** Check if there is a pending intended action */
  hasIntendedAction(): boolean {
    return !!this.loadIntendedAction();
  }

  /** Get the route to redirect to after login (from intended action or default) */
  getPostLoginRoute(): string {
    const action = this.loadIntendedAction();
    return action?.route || '/home';
  }

  private loadIntendedAction(): IntendedAction | null {
    try {
      const raw = localStorage.getItem(INTENDED_ACTION_KEY);
      if (!raw) return null;
      const action = JSON.parse(raw) as IntendedAction;
      // Expire after 30 minutes
      if (Date.now() - action.timestamp > 30 * 60 * 1000) {
        localStorage.removeItem(INTENDED_ACTION_KEY);
        return null;
      }
      return action;
    } catch {
      return null;
    }
  }
}
