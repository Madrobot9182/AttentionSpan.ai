import React from 'react'
import { observer } from 'mobx-react-lite'
import projectStore from '../ProjectStore'

const Market: React.FC = observer(() => {
    const seeds = [
        { type: 'sunflower', cost: 10 },
        { type: 'carrot', cost: 15 },
        { type: 'tomato', cost: 20 },
    ]

    return (
        <div className="market">
            <h3>Market</h3>
            <p>Coins: {projectStore.coins}</p>
            {seeds.map(seed => (
                <div key={seed.type}>
                    {seed.type} - {seed.cost} coins
                    <button onClick={() => projectStore.buySeed(seed.type, seed.cost)}>
                        Buy
                    </button>
                </div>
            ))}
        </div>
    )
})

export default Market
