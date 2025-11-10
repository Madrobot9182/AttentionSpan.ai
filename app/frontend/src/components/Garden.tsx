import React, { useState, useEffect, useRef } from 'react'
import { observer } from 'mobx-react-lite'
import projectStore, { type Seed } from '../ProjectStore'
import './Garden.css'
import Snackbar from '@mui/material/Snackbar'
import { observable } from 'mobx'
import { Plant } from './Plant'

const Garden: React.FC = observer(() => {
    const [growthStage, setGrowthStage] = useState(0)
    const canvasRef = useRef<HTMLCanvasElement | null>(null)
    const PADDING = 15
    const GRID_ROWS = 7
    const GRID_COLS = 7
    const [snackbarOpen, setSnackbarOpen] = useState(false)
    const [snackbarMessage, setSnackbarMessage] = useState('')
    const [sellHistory, setSellHistory] = useState<string[]>([])
    const [selectedSeed, setSelectedSeed] = useState<string | null>(null)
    const [isChoosingSeed, setIsChoosingSeed] = useState(false);

    // Menu state
    const [menuVisible, setMenuVisible] = useState(false)
    const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 })
    const [selectedCell, setSelectedCell] = useState<{ row: number; col: number } | null>(null)

    // Grid state
    const [grid, setGrid] = useState<(string | Plant)[][]>(() => {
        const centerRow = Math.floor(GRID_ROWS / 2)
        const centerCol = Math.floor(GRID_COLS / 2)
        return Array.from({ length: GRID_ROWS }, (_, r) =>
            Array.from({ length: GRID_COLS }, (_, c) => {
                if (r === centerRow && c === centerCol) return 'grass'
                const rand = Math.random()
                if (rand < 0.3) return 'rock'
                return 'grass'
            })
        )
    })

    useEffect(() => {
        if (!projectStore.isStudying) return;

        const growInterval = setInterval(() => {
            setGrid(prevGrid => {
                return prevGrid.map(row =>
                    row.map(cell => {
                        if (cell instanceof Plant) {
                            const justFullyGrown = cell.grow();

                            if (justFullyGrown && cell.isFullyGrown) {
                                const earned = cell.sell();
                                projectStore.coins += earned;

                                const now = new Date();
                                const plantedAtStr = cell.plantedAt.toLocaleTimeString();
                                const soldAtStr = now.toLocaleTimeString();
                                // Defer state updates

                                setSellHistory(prev => [
                                    `💰 Sold ${cell.type.name} for ${earned} coins (Planted: ${plantedAtStr}, Sold: ${soldAtStr})`,
                                    ...prev,
                                ]);

                                // Auto replant logic for grid (directly return new Plant)
                                // const inv: Seed[] = projectStore.inventory
                                // const seed = projectStore.inventory.find(s => s.type === cell.type.name);
                                // if (seed) {
                                //     seed.amount -=1
                                //     return new Plant(cell.type.name);
                                // }

                                return 'soil';
                            }

                            return cell;
                        }

                        return cell;
                    })
                );
            });

        }, 1000); // every 1 sec

        return () => clearInterval(growInterval);
    }, [projectStore.isStudying]);


    // Draw grid + plants
    const drawGrid = () => {
        const canvas = canvasRef.current
        if (!canvas) return
        const ctx = canvas.getContext('2d')
        if (!ctx) return

        const parent = canvas.parentElement
        if (!parent) return

        const { width, height } = parent.getBoundingClientRect()
        canvas.width = width
        canvas.height = height

        const actualCellWidth = (width - PADDING * 2) / GRID_COLS
        const actualCellHeight = (height - PADDING * 2) / GRID_ROWS

        ctx.clearRect(0, 0, width, height)

        for (let r = 0; r < GRID_ROWS; r++) {
            for (let c = 0; c < GRID_COLS; c++) {
                const x = PADDING + c * actualCellWidth
                const y = PADDING + r * actualCellHeight
                const cell = grid[r][c]
                const isPlant = cell instanceof Plant
                const terrain = isPlant ? 'plant' : cell

                let fillStyle
                switch (terrain) {
                    case 'rock':
                        fillStyle = '#8a8a8a'
                        break
                    case 'grass':
                        fillStyle = '#7bb661'
                        break
                    case 'soil':
                        fillStyle = '#a97142'
                        break
                    case 'plant':
                        fillStyle = '#a97142'
                        break
                    default:
                        fillStyle = '#ccc'
                }

                ctx.fillStyle = fillStyle
                ctx.fillRect(x, y, actualCellWidth, actualCellHeight)
                ctx.strokeStyle = 'rgba(50, 50, 50, 0.3)'
                ctx.lineWidth = 1
                ctx.strokeRect(x, y, actualCellWidth, actualCellHeight)

                if (isPlant && cell instanceof Plant) {
                    const plant = cell
                    const cellCenterX = x + actualCellWidth / 2
                    const cellCenterY = y + actualCellHeight / 2

                    // 🌿 Stage changes every ~33% of total growth
                    const progress = plant.growthTime / plant.type.maxGrowthTime
                    let stage = 0
                    if (progress >= 0.66) stage = 2
                    else if (progress >= 0.33) stage = 1
                    const emoji = plant.type.emojiArr[stage]

                    ctx.font = `${Math.floor(actualCellHeight * 0.6)}px serif`
                    ctx.textAlign = 'center'
                    ctx.textBaseline = 'middle'
                    ctx.fillText(emoji, cellCenterX, cellCenterY)
                }
            }
        }
    }

    useEffect(() => {
        drawGrid()
        window.addEventListener('resize', drawGrid)
        return () => window.removeEventListener('resize', drawGrid)
    }, [growthStage, grid])

    // Handle click: open menu if clicking rock/grass
    // Handle click: show menu depending on terrain
    const handleClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
        const canvas = canvasRef.current
        if (!canvas) return
        const container = canvas.parentElement
        if (!container) return

        const rect = container.getBoundingClientRect()
        const x = event.clientX - rect.left
        const y = event.clientY - rect.top

        const cellWidth = (canvas.width - PADDING * 2) / GRID_COLS
        const cellHeight = (canvas.height - PADDING * 2) / GRID_ROWS

        const col = Math.floor((x - PADDING) / cellWidth)
        const row = Math.floor((y - PADDING) / cellHeight)

        if (row < 0 || row >= GRID_ROWS || col < 0 || col >= GRID_COLS) return

        const terrain = grid[row][col]

        if (terrain === 'rock' || terrain === 'grass' || terrain === 'soil') {
            // Approximate menu size
            const menuWidth = 160
            const menuHeight = 40

            let menuX = x
            let menuY = y

            // constrain horizontally
            if (menuX + menuWidth > rect.width) {
                menuX = rect.width - menuWidth - 8
            }

            // constrain vertically
            if (menuY + menuHeight > rect.height) {
                menuY = rect.height - menuHeight - 8
            }

            setMenuPosition({ x: menuX, y: menuY })
            setSelectedCell({ row, col })
            setMenuVisible(true)
        } else {
            setMenuVisible(false)
        }
    }

    // Clear a tile (convert to soil)
    const handleRemoveTile = () => {
        if (!selectedCell) return
        if (projectStore.coins < 50) {
            setSnackbarMessage('Not enough coins! You need 50 coins.')
            setSnackbarOpen(true)
            setMenuVisible(false)

            return
        }
        projectStore.coins -= 50
        const { row, col } = selectedCell
        setGrid(prev => {
            const newGrid = prev.map(r => [...r])
            newGrid[row][col] = 'soil'
            return newGrid
        })
        setMenuVisible(false)
    }

    const handleAddPlant = () => {
        if (!selectedCell) return;

        if (projectStore.inventory.length === 0) {
            setSnackbarMessage("You don't have any seeds!");
            setSnackbarOpen(true);
            setMenuVisible(false);
            return;
        }

        // Show seed selection menu instead of normal menu
        setIsChoosingSeed(true);
    };




    // Close menu on outside click
    useEffect(() => {
        const handleOutside = (event: MouseEvent) => {
            const menu = document.querySelector('.garden-menu')
            if (menu && !menu.contains(event.target as Node)) {
                setMenuVisible(false)
            }
        }
        if (menuVisible) document.addEventListener('click', handleOutside)
        return () => document.removeEventListener('click', handleOutside)
    }, [menuVisible])

    // Inside Garden.tsx, just before the return statement
    const marketItems = [
        { type: 'sunflower', cost: 10 },
        { type: 'carrot', cost: 15 },
        { type: 'tomato', cost: 20 },
    ];

    return (
        <div className="garden-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Garden Canvas */}
            <div className="garden-section" style={{ position: 'relative' }}>
                <canvas
                    ref={canvasRef}
                    className="garden-canvas"
                    onClick={(e) => { e.stopPropagation(); handleClick(e); }}
                />
                {menuVisible && selectedCell && (
                    <div
                        className="garden-menu"
                        style={{ top: menuPosition.y, left: menuPosition.x }}
                        onClick={e => e.stopPropagation()}
                    >
                        {!isChoosingSeed ? (
                            (() => {
                                const terrain = grid[selectedCell.row][selectedCell.col];

                                if (terrain === 'rock' || terrain === 'grass') {
                                    return <button onClick={handleRemoveTile}>🪓 Remove {terrain}: 50 Coins</button>;
                                }

                                if (terrain === 'soil') {
                                    return <button onClick={handleAddPlant}>🌱 Add Plant</button>;
                                }

                                return null;
                            })()
                        ) : (
                            <>
                                <h4>Select Seed</h4>
                                {projectStore.inventory
                                    .filter(seed => seed.amount > 0)
                                    .map(seed => (
                                        <button
                                            key={seed.type}
                                            onClick={() => {
                                                const plant = new Plant(seed.type);
                                                setGrid(prev => {
                                                    const newGrid = prev.map(r => [...r]);
                                                    const { row, col } = selectedCell;
                                                    newGrid[row][col] = plant;
                                                    return newGrid;
                                                });

                                                // Remove seed from inventory
                                                projectStore.removeSeed(seed.type);

                                                // Close menu
                                                setIsChoosingSeed(false);
                                                setMenuVisible(false);
                                            }}
                                        >
                                            {seed.type} x{seed.amount}
                                        </button>
                                    ))}
                            </>
                        )}
                    </div>
                )}


                <Snackbar
                    open={snackbarOpen}
                    autoHideDuration={3000}
                    onClose={() => setSnackbarOpen(false)}
                    message={snackbarMessage}
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
                />
            </div>


            {/* Inventory Panel */}
            <div
                className="inventory"
                style={{
                    padding: '10px',
                    backgroundColor: '#f0f9f0',
                    borderRadius: '8px',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.1)'
                }}
            >
                <h3>Inventory</h3>
                {projectStore.inventory.length === 0 ? (
                    <p>Empty</p>
                ) : (
                    <ul>
                        {projectStore.inventory.map(seed => (
                            <li key={seed.type}>
                                {seed.type} x{seed.amount}
                            </li>
                        ))}
                    </ul>
                )}
            </div>


            {/* Market Panel */}
            <div
                className="market"
                style={{
                    padding: '10px',
                    backgroundColor: '#f9f0f0',
                    borderRadius: '8px',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.1)'
                }}
            >
                <h3>Market</h3>
                <p>Coins: {projectStore.coins}</p>
                {marketItems.map(item => (
                    <div key={item.type} style={{ marginBottom: '8px' }}>
                        {item.type} - {item.cost} coins
                        <button
                            style={{ marginLeft: '10px', padding: '4px 8px', borderRadius: '4px' }}
                            onClick={() => {
                                if (projectStore.coins >= item.cost) {
                                    projectStore.coins -= item.cost;
                                    const existing = projectStore.inventory.find(seed => seed.type === item.type);
                                    if (existing) {
                                        existing.amount += 1;
                                    } else {
                                        projectStore.inventory.push({ type: item.type, amount: 1 });
                                    }
                                } else {
                                    alert('Not enough coins!');
                                }
                            }}
                        >
                            Buy
                        </button>
                    </div>
                ))}
            </div>

            {/* Sell History Panel */}
            <div className="garden-history">
                <h3>Sell History</h3>
                {sellHistory.length === 0 ? (
                    <p className="empty-history">No sales yet</p>
                ) : (
                    <ul>
                        {sellHistory.map((entry, index) => (
                            <li key={index}>{entry}</li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );




})

export default observable(Garden)