// ProjectStore.ts
import { makeAutoObservable, makeObservable, observable } from "mobx";

export interface Seed {
  type: string
  amount: number
}

class ProjectStore {
  isStudying: boolean = false;
  time: number = 0;
  coins: number = 1000;
  inventory: Seed[] = []
  constructor() {
    makeAutoObservable(this);
  }

  addSeed(type: string, amount: number = 5) {
    const seed = this.inventory.find(s => s.type === type)
    if (seed) seed.amount += amount
    else this.inventory.push({ type, amount })
  }

  removeSeed(type: string, amount: number = 1) {
    const seed = this.inventory.find(s => s.type === type)
    if (!seed || seed.amount < amount) return false
    seed.amount -= amount
    if (seed.amount === 0) this.inventory = this.inventory.filter(s => s.amount > 0)
    return true
  }

  buySeed(type: string, cost: number, amount: number = 1) {
    if (this.coins >= cost * amount) {
      this.coins -= cost * amount
      this.addSeed(type, amount)
      return true
    }
    return false
  }

  toggle(): void {
    this.isStudying = !this.isStudying;
  }
}

const projectStore = new ProjectStore();
export default projectStore;