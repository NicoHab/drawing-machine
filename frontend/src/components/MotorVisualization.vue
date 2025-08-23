<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'

// Props
interface Props {
  motorStates: Record<string, any>
  blockchainData?: any
  isActive: boolean
}

const props = defineProps<Props>()

// Motor visualization state
const canvasRef = ref<HTMLCanvasElement | null>(null)
const ctx = ref<CanvasRenderingContext2D | null>(null)
const animationId = ref<number | null>(null)

// Motor positions and state
const motors = ref([
  { 
    key: 'motor_canvas', 
    name: 'Canvas', 
    x: 150, 
    y: 150, 
    angle: 0, 
    color: '#3498db',
    velocity: 0,
    direction: 'CW',
    lastUpdate: 0
  },
  { 
    key: 'motor_pb', 
    name: 'PB', 
    x: 450, 
    y: 150, 
    angle: 0, 
    color: '#27ae60',
    velocity: 0,
    direction: 'CW', 
    lastUpdate: 0
  },
  { 
    key: 'motor_pcd', 
    name: 'PCD', 
    x: 150, 
    y: 300, 
    angle: 0, 
    color: '#9b59b6',
    velocity: 0,
    direction: 'CW',
    lastUpdate: 0
  },
  { 
    key: 'motor_pe', 
    name: 'PE', 
    x: 450, 
    y: 300, 
    angle: 0, 
    color: '#e67e22',
    velocity: 0,
    direction: 'CW',
    lastUpdate: 0
  }
])

const radius = 40

// Update motor states when props change
watch(() => props.motorStates, (newStates) => {
  if (!newStates) return
  
  motors.value.forEach(motor => {
    const state = newStates[motor.key]
    if (state) {
      motor.velocity = state.velocity_rpm || 0
      motor.direction = state.direction || 'CW'
      motor.lastUpdate = state.last_update || Date.now() / 1000
    }
  })
}, { deep: true })

// Animation loop
const animate = () => {
  if (!ctx.value || !props.isActive) return
  
  // Clear canvas
  ctx.value.clearRect(0, 0, 600, 400)
  
  // Update and draw each motor
  motors.value.forEach(motor => {
    updateMotorRotation(motor)
    drawMotor(motor)
  })
  
  animationId.value = requestAnimationFrame(animate)
}

const updateMotorRotation = (motor: any) => {
  // Update rotation based on velocity and direction
  const rotationSpeed = Math.abs(motor.velocity) * 0.1 // Scale for visual effect
  const direction = motor.direction === 'CCW' ? -1 : 1
  
  motor.angle += rotationSpeed * direction
  if (motor.angle >= 360) motor.angle -= 360
  if (motor.angle < 0) motor.angle += 360
}

const drawMotor = (motor: any) => {
  if (!ctx.value) return
  
  const { x, y, angle, color, name, velocity, direction } = motor
  
  // Motor base circle
  ctx.value.beginPath()
  ctx.value.arc(x, y, radius, 0, 2 * Math.PI)
  ctx.value.fillStyle = '#f8f9fa'
  ctx.value.fill()
  ctx.value.strokeStyle = '#333'
  ctx.value.lineWidth = 2
  ctx.value.stroke()
  
  // Motor pointer/arm
  const rad = (angle * Math.PI) / 180
  const endX = x + (radius - 5) * Math.cos(rad)
  const endY = y + (radius - 5) * Math.sin(rad)
  
  // Activity-based color
  let activityColor = color
  if (Math.abs(velocity) > 15) activityColor = '#e74c3c'
  else if (Math.abs(velocity) > 10) activityColor = '#f39c12'
  else if (Math.abs(velocity) > 0) activityColor = '#27ae60'
  else activityColor = '#95a5a6'
  
  ctx.value.beginPath()
  ctx.value.moveTo(x, y)
  ctx.value.lineTo(endX, endY)
  ctx.value.strokeStyle = activityColor
  ctx.value.lineWidth = 4
  ctx.value.stroke()
  
  // Arrow head
  const arrowAngle = rad
  const arrowSize = 8
  ctx.value.beginPath()
  ctx.value.moveTo(endX, endY)
  ctx.value.lineTo(
    endX - arrowSize * Math.cos(arrowAngle - 0.3),
    endY - arrowSize * Math.sin(arrowAngle - 0.3)
  )
  ctx.value.lineTo(
    endX - arrowSize * Math.cos(arrowAngle + 0.3),
    endY - arrowSize * Math.sin(arrowAngle + 0.3)
  )
  ctx.value.closePath()
  ctx.value.fillStyle = activityColor
  ctx.value.fill()
  
  // Motor name
  ctx.value.fillStyle = '#333'
  ctx.value.font = 'bold 14px Arial'
  ctx.value.textAlign = 'center'
  ctx.value.fillText(name, x, y + radius + 20)
  
  // RPM display with sign
  const rpmDisplay = direction === 'CCW' ? `-${velocity.toFixed(1)}` : `${velocity.toFixed(1)}`
  ctx.value.fillStyle = '#666'
  ctx.value.font = '12px Arial'
  ctx.value.fillText(`${rpmDisplay} RPM`, x, y + radius + 35)
  
  // Blockchain data (if available)
  if (props.blockchainData) {
    const dataText = getMotorDataText(motor.key)
    if (dataText) {
      ctx.value.fillStyle = '#888'
      ctx.value.font = '10px Arial'
      ctx.value.fillText(dataText, x, y + radius + 48)
    }
  }
}

const getMotorDataText = (motorKey: string) => {
  if (!props.blockchainData) return ''
  
  const data = props.blockchainData
  switch (motorKey) {
    case 'motor_canvas':
      return `ETH: $${data.eth_price_usd?.toFixed(2) || '0.00'}`
    case 'motor_pb':
      return `Gas: ${data.gas_price_gwei?.toFixed(3) || '0.000'} gwei`
    case 'motor_pcd':
      return `Blob: ${data.blob_space_utilization_percent?.toFixed(1) || '0.0'}%`
    case 'motor_pe':
      return `Block: ${data.block_fullness_percent?.toFixed(1) || '0.0'}%`
    default:
      return ''
  }
}

// Lifecycle
onMounted(() => {
  if (canvasRef.value) {
    ctx.value = canvasRef.value.getContext('2d')
    if (props.isActive) {
      animate()
    }
  }
})

onUnmounted(() => {
  if (animationId.value) {
    cancelAnimationFrame(animationId.value)
  }
})

// Watch for active state changes
watch(() => props.isActive, (isActive) => {
  if (isActive && ctx.value && !animationId.value) {
    animate()
  } else if (!isActive && animationId.value) {
    cancelAnimationFrame(animationId.value)
    animationId.value = null
  }
})

// Stats computed values
const totalCommands = computed(() => {
  return motors.value.reduce((sum, motor) => {
    const state = props.motorStates[motor.key]
    return sum + (state?.total_commands || 0)
  }, 0)
})

const activeMotors = computed(() => {
  return motors.value.filter(motor => Math.abs(motor.velocity) > 0.1).length
})
</script>

<template>
  <div class="motor-visualization">
    <div class="viz-header">
      <h3>🎨 Real-time Motor Visualization</h3>
      <div class="viz-stats">
        <span class="stat">Active: {{ activeMotors }}/4</span>
        <span class="stat">Commands: {{ totalCommands }}</span>
        <span class="stat" v-if="blockchainData">
          Block: {{ blockchainData.block_number || 'N/A' }}
        </span>
      </div>
    </div>
    
    <div class="canvas-container">
      <canvas 
        ref="canvasRef"
        width="600" 
        height="400"
        :class="{ active: isActive }"
      ></canvas>
      
      <div v-if="!isActive" class="overlay">
        <div class="overlay-content">
          <h4>🔌 Visualization Paused</h4>
          <p>Connect to see real-time motor movement</p>
        </div>
      </div>
    </div>
    
    <!-- Blockchain Data Panel (if available) -->
    <div v-if="blockchainData" class="blockchain-panel">
      <h4>📊 Live Blockchain Data</h4>
      <div class="data-grid">
        <div class="data-item">
          <span class="label">ETH Price:</span>
          <span class="value">${{ blockchainData.eth_price_usd?.toFixed(2) || '0.00' }}</span>
        </div>
        <div class="data-item">
          <span class="label">Gas Price:</span>
          <span class="value">{{ blockchainData.gas_price_gwei?.toFixed(3) || '0.000' }} gwei</span>
        </div>
        <div class="data-item">
          <span class="label">Blob Utilization:</span>
          <span class="value">{{ blockchainData.blob_space_utilization_percent?.toFixed(1) || '0.0' }}%</span>
        </div>
        <div class="data-item">
          <span class="label">Block Fullness:</span>
          <span class="value">{{ blockchainData.block_fullness_percent?.toFixed(1) || '0.0' }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.motor-visualization {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.viz-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #ecf0f1;
}

.viz-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
}

.viz-stats {
  display: flex;
  gap: 15px;
}

.stat {
  font-size: 12px;
  padding: 4px 8px;
  background: #ecf0f1;
  border-radius: 4px;
  color: #7f8c8d;
  font-weight: 500;
}

.canvas-container {
  position: relative;
  text-align: center;
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
}

canvas {
  border: 1px solid #ddd;
  background: white;
  transition: opacity 0.3s;
}

canvas.active {
  opacity: 1;
}

canvas:not(.active) {
  opacity: 0.3;
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
}

.overlay-content {
  text-align: center;
  color: #7f8c8d;
}

.overlay-content h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
}

.overlay-content p {
  margin: 0;
  font-size: 14px;
}

.blockchain-panel {
  margin-top: 20px;
  padding: 15px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.blockchain-panel h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  opacity: 0.9;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
}

.data-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  padding: 4px 0;
}

.label {
  opacity: 0.8;
}

.value {
  font-weight: bold;
  font-family: 'Courier New', monospace;
}

@media (max-width: 768px) {
  canvas {
    width: 100%;
    height: auto;
  }
  
  .viz-header {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
  
  .viz-stats {
    justify-content: center;
  }
  
  .data-grid {
    grid-template-columns: 1fr;
  }
}
</style>