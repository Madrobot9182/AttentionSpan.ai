import React, { useState, useEffect, useRef } from 'react'
import { observer } from 'mobx-react-lite'
import projectStore from '../ProjectStore'
import './Garden.css'
import Snackbar from '@mui/material/Snackbar'
import { observable } from 'mobx'

const Garden: React.FC = observer(() => {
    const [growthStage, setGrowthStage] = useState(0)
    const canvasRef = useRef<HTMLCanvasElement | null>(null)
    const PADDING = 15
    const GRID_ROWS = 7
    const GRID_COLS = 7
    const [snackbarOpen, setSnackbarOpen] = useState(false)
    const [snackbarMessage, setSnackbarMessage] = useState('')

    // Menu state
    const [menuVisible, setMenuVisible] = useState(false)
    const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 })
    const [selectedCell, setSelectedCell] = useState<{ row: number; col: number } | null>(null)

    // Grid state
    const [grid, setGrid] = useState<string[][]>(() => {
        const centerRow = Math.floor(GRID_ROWS / 2)
        const centerCol = Math.floor(GRID_COLS / 2)
        return Array.from({ length: GRID_ROWS }, (_, r) =>
            Array.from({ length: GRID_COLS }, (_, c) => {
                if (r === centerRow && c === centerCol) return 'plant'
                const rand = Math.random()
                if (rand < 0.3) return 'rock'
                return 'grass'
            })
        )
    })

    // Growth logic (plant grows if studying)
    useEffect(() => {
        let timer: ReturnType<typeof setInterval>
        if (projectStore.isStudying) {
            timer = setInterval(() => {
                setGrowthStage(prev => Math.min(prev + 1, 2))
            }, 10000)
        } else {
            setGrowthStage(0)
        }
        return () => clearInterval(timer)
    }, [projectStore.isStudying])

    const plantEmoji = ['🌱', '🌿', '🌳'][growthStage] || '🌱'

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
                const terrain = grid[r][c]

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

                if (terrain === 'plant') {
                    const cellCenterX = x + actualCellWidth / 2
                    const cellCenterY = y + actualCellHeight / 2
                    ctx.font = `${Math.floor(actualCellHeight * 0.6)}px serif`
                    ctx.textAlign = 'center'
                    ctx.textBaseline = 'middle'
                    ctx.fillText(plantEmoji, cellCenterX, cellCenterY)
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
        projectStore.coins -=50
        console.log(projectStore.coins)
        const { row, col } = selectedCell
        setGrid(prev => {
            const newGrid = prev.map(r => [...r])
            newGrid[row][col] = 'soil'
            return newGrid
        })
        setMenuVisible(false)
    }

    const handleAddPlant = () => {
        if (!selectedCell) return
        const { row, col } = selectedCell
        setGrid(prev => {
            const newGrid = prev.map(r => [...r])
            newGrid[row][col] = 'plant'
            return newGrid
        })
        setMenuVisible(false)
    }

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

    return (
        <div className="garden-section">
            <canvas
                ref={canvasRef}
                className="garden-canvas"
                onClick={(e) => { e.stopPropagation(); handleClick(e); }}
            />
            {menuVisible && selectedCell && (
                <div
                    className="garden-menu"
                    style={{ top: menuPosition.y, left: menuPosition.x }}
                    onClick={e => e.stopPropagation()} // prevent closing when clicking the menu
                >
                    {(() => {
                        const terrain = grid[selectedCell.row][selectedCell.col]

                        // If tile is rock/grass → show "Remove" button
                        if (terrain === 'rock' || terrain === 'grass') {
                            return <button onClick={handleRemoveTile}>🪓 Remove Cost: 50 Coins</button>
                        }

                        // If tile is soil → show "Add Plant" button
                        if (terrain === 'soil') {
                            return <button onClick={handleAddPlant}>🌱 Add Plant</button>
                        }

                        return null
                    })()}
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
    )
})

export default observable(Garden)