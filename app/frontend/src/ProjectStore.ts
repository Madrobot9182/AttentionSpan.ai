// ProjectStore.ts
import { makeAutoObservable } from "mobx";

class ProjectStore {
  isStudying: boolean = false;
  time: number = 0;

  constructor() {
    makeAutoObservable(this);
  }

  toggle(): void {
    this.isStudying = !this.isStudying;
  }
}

const projectStore = new ProjectStore();
export default projectStore;