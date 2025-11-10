// ProjectStore.ts
import { makeAutoObservable } from "mobx";

class ProjectStore {
  isStudying: boolean = false;
  time: number = 0;
  focusLabel: string | null = null
  focusConfidence: number | null = null

  constructor() {
    makeAutoObservable(this);
  }

  toggle(): void {
    this.isStudying = !this.isStudying;
  }

  setFocusLabel(label: string | null, confidence?: number | null) {
    this.focusLabel = label
    if (confidence !== undefined) {
      this.focusConfidence = confidence
    }
  }

  resetFocus() {
    this.focusLabel = null
    this.focusConfidence = null
  }
}

const projectStore = new ProjectStore();
export default projectStore;