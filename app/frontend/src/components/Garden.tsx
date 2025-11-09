import React, { useState, useEffect, useRef } from 'react'
import { observer } from 'mobx-react-lite'
import projectStore from '../ProjectStore'
import './Garden.css'

const Garden: React.FC = observer(() => {
  const [growthStage, setGrowthStage] = useState(0)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const CELL_SIZE = 50
  const PADDING = 15 // space inside edges

  // Growth logic
  useEffect(() => {
    let timer: ReturnType<typeof setInterval>
    if (projectStore.isStudying) {
      timer = setInterval(() => {
        setGrowthStage(prev => Math.min(prev + 1, 3))
      }, 10000)
    } else {
      setGrowthStage(0)
    }
    return () => clearInterval(timer)
  }, [projectStore.isStudying])

  const plantEmoji = ['🌱', '🌿', '🌳'][growthStage] || '🌱'

  // Draw grid and plant
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

        // Compute max number of rows and columns that fit inside the canvas with padding
        const cols = Math.floor((width - PADDING * 2) / CELL_SIZE)
        const rows = Math.floor((height - PADDING * 2) / CELL_SIZE)

        // Adjust actual cell size to perfectly fit the canvas
        const actualCellWidth = (width - PADDING * 2) / cols
        const actualCellHeight = (height - PADDING * 2) / rows

        ctx.clearRect(0, 0, width, height)

        // Draw vertical lines
        ctx.strokeStyle = 'rgba(80, 122, 82, 0.4)'
        ctx.lineWidth = 1
        for (let c = 0; c <= cols; c++) {
            const x = PADDING + c * actualCellWidth
            ctx.beginPath()
            ctx.moveTo(x, PADDING)
            ctx.lineTo(x, height - PADDING)
            ctx.stroke()
        }

        // Draw horizontal lines
        for (let r = 0; r <= rows; r++) {
            const y = PADDING + r * actualCellHeight
            ctx.beginPath()
            ctx.moveTo(PADDING, y)
            ctx.lineTo(width - PADDING, y)
            ctx.stroke()
        }

        // Draw example plant in top-left cell
        ctx.font = '32px serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        const cellCenterX = PADDING + actualCellWidth / 2
        const cellCenterY = PADDING + actualCellHeight / 2
        ctx.fillText(plantEmoji, cellCenterX, cellCenterY)
    }



    drawGrid()
    window.addEventListener('resize', drawGrid)
    return () => window.removeEventListener('resize', drawGrid)
  }, [growthStage])

  return (
    <div className="garden-section">
      <canvas ref={canvasRef} className="garden-canvas" />
    </div>
  )
})

export default Garden
