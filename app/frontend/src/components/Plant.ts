export type PlantType = {
  name: string;
  baseValue: number;     // how much it sells for
  maxGrowthTime: number; // time required to grow (seconds / ticks / etc.)
  emojiArr: Array<string>;
};

export const PLANT_TYPES: Record<string, PlantType> = {
  sunflower: { name: "Sunflower", baseValue: 10, maxGrowthTime: 30, emojiArr: ['🟢', '🌱','🌻'] },
  carrot: { name: "Carrot", baseValue: 4, maxGrowthTime: 3, emojiArr: ['🟢', '🌱','🥕']  },
  rose: { name: "Rose", baseValue: 12, maxGrowthTime: 6 , emojiArr: ['🟢', '🌱','🌹'] },
  tomato: { name: "Tomato", baseValue: 8, maxGrowthTime: 4 , emojiArr: ['🟢', '🌱','🍅'] },
};

export class Plant {
  typeName: string;
  type: PlantType;          // the data struct from PLANT_TYPES
  growthTime: number = 0;   // how long it has been growing
  isFullyGrown: boolean = false;
  plantedAt: Date = new Date;

  constructor(typeName: string) {
    this.typeName = typeName.toLowerCase();

    // Look up the type data from PLANT_TYPES
    const plantData = PLANT_TYPES[this.typeName];
    if (!plantData) {
      throw new Error(`Unknown plant type: ${typeName}`);
    }

    this.type = plantData;
    this.plantedAt = new Date()
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

  // sell and reset
  sell(): number {
    if (!this.isFullyGrown) return 0;

    const value = this.type.baseValue;

    // Reset / replant
    this.growthTime = 0;
    this.isFullyGrown = false;

    return value;
  }
}
