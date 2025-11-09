// ProjectStore.ts
import { makeAutoObservable, makeObservable, observable } from "mobx";

class ProjectStore {
  isStudying: boolean = false;
  time: number = 0;
  coins: number = 1000;

  constructor() {
    makeAutoObservable(this);
  }

  toggle(): void {
    this.isStudying = !this.isStudying;
  }
}

const projectStore = new ProjectStore();
export default projectStore;