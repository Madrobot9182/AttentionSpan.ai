import React, { useState, useEffect, useRef } from 'react'
import { observer } from 'mobx-react-lite'
import projectStore from '../ProjectStore'
import './Garden.css'

const Garden: React.FC = observer(() => {
  const [growthStage, setGrowthStage] = useState(0)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  const CELL_SIZE = 50
  const PADDING = 15
  const GRID_ROWS = 7
  const GRID_COLS = 7

  // Create a grid where only the center is soil
  const [grid, setGrid] = useState<string[][]>(() => {
    const gridArray = Array.from({ length: GRID_ROWS }, (_, r) =>
      Array.from({ length: GRID_COLS }, (_, c) => {
        const centerRow = Math.floor(GRID_ROWS / 2)
        const centerCol = Math.floor(GRID_COLS / 2)
        if (r === centerRow && c === centerCol) return 'soil'
        // Randomize between rock/grass for the rest
        const rand = Math.random()
        if (rand < 0.3) return 'rock'
        return 'grass'
      })
    )
    return gridArray
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

  // Draw grid and plants
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const drawGrid = () => {
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

          // Terrain colors
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
            default:
              fillStyle = '#ccc'
          }

          ctx.fillStyle = fillStyle
          ctx.fillRect(x, y, actualCellWidth, actualCellHeight)

          // Cell borders
          ctx.strokeStyle = 'rgba(50, 50, 50, 0.3)'
          ctx.lineWidth = 1
          ctx.strokeRect(x, y, actualCellWidth, actualCellHeight)

          // Plant only on soil
          if (terrain === 'soil') {
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

    drawGrid()
    window.addEventListener('resize', drawGrid)
    return () => window.removeEventListener('resize', drawGrid)
  }, [growthStage, grid])

  return (
    <div className="garden-section">
      <canvas ref={canvasRef} className="garden-canvas" />
    </div>
  )
})

export default Garden
