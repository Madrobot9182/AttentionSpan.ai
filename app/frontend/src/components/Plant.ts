export type PlantType = {
    name: string;
    baseValue: number;     // how much it sells for
    maxGrowthTime: number; // time required to grow (seconds / ticks / etc.)
};


export const PLANT_TYPES: Record<string, PlantType> = {
sunflower: { name: "Sunflower", baseValue: 10, maxGrowthTime: 5 },
carrot: { name: "Carrot", baseValue: 4, maxGrowthTime: 3 },
rose: { name: "Rose", baseValue: 12, maxGrowthTime: 6 },
tomato: { name: "Tomato", baseValue: 8, maxGrowthTime: 4 }
};  

export class Plant {
    type: PlantType;
    growthTime: number = 0; // how long it has been growing
    isFullyGrown: boolean = false;
  
    constructor(type: PlantType) {
      this.type = type;
    }
  
    // increments growth by 1 tick
    grow(): boolean {
      if (this.isFullyGrown) return false;
  
      this.growthTime++;
  
      if (this.growthTime >= this.type.maxGrowthTime) {
        this.isFullyGrown = true;
        return true; // ready to sell
      }
      return false;
    }
  
    sell(): number {
      if (!this.isFullyGrown) return 0;
  
      const value = this.type.baseValue;
  
      // Reset / replant
      this.growthTime = 0;
      this.isFullyGrown = false;
  
      return value;
    }
  }
  