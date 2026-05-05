import { Injectable } from '@angular/core';
import { Preferences } from '@capacitor/preferences';
import { BehaviorSubject } from 'rxjs';

const WELCOME_COMPLETED_KEY = 'freelancehub_welcome_completed';
const TOUR_COMPLETED_KEY = 'freelancehub_tour_completed';
const SELECTED_INTENT_KEY = 'freelancehub_selected_intent';

export type UserIntent = 'hiring' | 'freelancing' | 'browsing' | null;

@Injectable({ providedIn: 'root' })
export class OnboardingStateService {
  private welcomeCompleted$ = new BehaviorSubject<boolean>(false);
  private tourCompleted$ = new BehaviorSubject<boolean>(false);
  private selectedIntent$ = new BehaviorSubject<UserIntent>(null);

  constructor() {
    this.loadState();
  }

  // ── Welcome Slides ──────────────────────────

  get isWelcomeCompleted(): boolean {
    return this.welcomeCompleted$.value;
  }

  async markWelcomeCompleted(): Promise<void> {
    await Preferences.set({ key: WELCOME_COMPLETED_KEY, value: 'true' });
    localStorage.setItem(WELCOME_COMPLETED_KEY, 'true');
    this.welcomeCompleted$.next(true);
  }

  // ── Quick Tour ──────────────────────────────

  get isTourCompleted(): boolean {
    return this.tourCompleted$.value;
  }

  async markTourCompleted(): Promise<void> {
    await Preferences.set({ key: TOUR_COMPLETED_KEY, value: 'true' });
    localStorage.setItem(TOUR_COMPLETED_KEY, 'true');
    this.tourCompleted$.next(true);
  }

  async resetTour(): Promise<void> {
    await Preferences.remove({ key: TOUR_COMPLETED_KEY });
    localStorage.removeItem(TOUR_COMPLETED_KEY);
    this.tourCompleted$.next(false);
  }

  // ── User Intent ─────────────────────────────

  get selectedIntent(): UserIntent {
    return this.selectedIntent$.value;
  }

  async setIntent(intent: UserIntent): Promise<void> {
    if (intent) {
      await Preferences.set({ key: SELECTED_INTENT_KEY, value: intent });
      localStorage.setItem(SELECTED_INTENT_KEY, intent);
    } else {
      await Preferences.remove({ key: SELECTED_INTENT_KEY });
      localStorage.removeItem(SELECTED_INTENT_KEY);
    }
    this.selectedIntent$.next(intent);
  }

  // ── Load persisted state ────────────────────

  private async loadState(): Promise<void> {
    try {
      // Try Capacitor Preferences first, fallback to localStorage
      const welcomeRes = await Preferences.get({ key: WELCOME_COMPLETED_KEY });
      const tourRes = await Preferences.get({ key: TOUR_COMPLETED_KEY });
      const intentRes = await Preferences.get({ key: SELECTED_INTENT_KEY });

      this.welcomeCompleted$.next(
        welcomeRes.value === 'true' || localStorage.getItem(WELCOME_COMPLETED_KEY) === 'true'
      );
      this.tourCompleted$.next(
        tourRes.value === 'true' || localStorage.getItem(TOUR_COMPLETED_KEY) === 'true'
      );

      const intent = (intentRes.value || localStorage.getItem(SELECTED_INTENT_KEY)) as UserIntent;
      this.selectedIntent$.next(intent);
    } catch {
      // Fallback to localStorage only
      this.welcomeCompleted$.next(localStorage.getItem(WELCOME_COMPLETED_KEY) === 'true');
      this.tourCompleted$.next(localStorage.getItem(TOUR_COMPLETED_KEY) === 'true');
      this.selectedIntent$.next(localStorage.getItem(SELECTED_INTENT_KEY) as UserIntent);
    }
  }

  // ── Full Reset (for testing) ────────────────

  async resetAll(): Promise<void> {
    await Preferences.remove({ key: WELCOME_COMPLETED_KEY });
    await Preferences.remove({ key: TOUR_COMPLETED_KEY });
    await Preferences.remove({ key: SELECTED_INTENT_KEY });
    localStorage.removeItem(WELCOME_COMPLETED_KEY);
    localStorage.removeItem(TOUR_COMPLETED_KEY);
    localStorage.removeItem(SELECTED_INTENT_KEY);
    this.welcomeCompleted$.next(false);
    this.tourCompleted$.next(false);
    this.selectedIntent$.next(null);
  }
}
