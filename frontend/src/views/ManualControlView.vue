<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import MotorControl from '../components/MotorControl.vue'
import MotorVisualization from '../components/MotorVisualization.vue'

// WebSocket connection
const ws = ref<WebSocket | null>(null)
const connectionStatus = ref<'disconnected' | 'connecting' | 'connected'>('disconnected')

// System state
const systemState = reactive({
  mode: 'manual',
  motorStates: {} as Record<string, any>,
  blockchainData: null as any
})

// Debounce mode changes to prevent loops
let lastModeChangeTime = 0

// Connection settings - Environment configurable
const wsUrl = ref(import.meta.env.VITE_BACKEND_URL || 'ws://localhost:8768')
const apiKey = ref('')

// Connect to WebSocket server
const connect = () => {
  if (ws.value?.readyState === WebSocket.OPEN) {
    return
  }

  connectionStatus.value = 'connecting'
  ws.value = new WebSocket(wsUrl.value)

  ws.value.onopen = () => {
    connectionStatus.value = 'connected'
    console.log(`Connected to server at ${wsUrl.value}`)
    
    // Send authentication immediately
    ws.value?.send(JSON.stringify({
      type: 'authenticate',
      client_type: 'web_ui',
      user_info: {},
      api_key: apiKey.value
    }))
  }

  ws.value.onmessage = (event) => {
    handleMessage(JSON.parse(event.data))
  }

  ws.value.onclose = () => {
    connectionStatus.value = 'disconnected'
    console.log('Disconnected from manual control server')
    
    // Auto-reconnect after 3 seconds
    setTimeout(connect, 3000)
  }

  ws.value.onerror = (error) => {
    console.error('WebSocket error:', error)
    connectionStatus.value = 'disconnected'
  }
}

// Disconnect from WebSocket
const disconnect = () => {
  if (ws.value) {
    ws.value.close()
    ws.value = null
  }
  connectionStatus.value = 'disconnected'
}

// Handle incoming WebSocket messages
const handleMessage = (data: any) => {
  console.log(`Received message type: ${data.type}`, data)
  
  switch (data.type) {
    case 'authenticated':
      console.log('Successfully authenticated with server:', data.message)
      if (data.api_access === false) {
        alert('Demo mode: Blockchain API disabled for cost control. Enter API key to enable live data.')
      }
      break
      
    case 'system_state':
      console.log('Updating system state:', data)
      Object.assign(systemState, {
        mode: data.mode,
        motorStates: data.motor_states || {
          motor_canvas: { velocity_rpm: 0, direction: 'CW', last_update: Date.now()/1000, is_enabled: true },
          motor_pb: { velocity_rpm: 0, direction: 'CW', last_update: Date.now()/1000, is_enabled: true },
          motor_pcd: { velocity_rpm: 0, direction: 'CW', last_update: Date.now()/1000, is_enabled: true },
          motor_pe: { velocity_rpm: 0, direction: 'CW', last_update: Date.now()/1000, is_enabled: true }
        }
      })
      
      // If we're in manual mode and just received system state, ensure motors are initialized
      if (data.mode === 'manual' && data.motor_states) {
        console.log('Manual mode detected - ensuring motor states are active')
      }
      break
    
    case 'motor_update':
      systemState.motorStates[data.motor_name] = data.state
      break
    
    case 'motor_command_executed':
      // Update our motor states when commands are executed
      if (data.command) {
        const motorName = data.command.motor_name
        if (motorName && systemState.motorStates[motorName]) {
          systemState.motorStates[motorName].velocity_rpm = data.command.velocity_rpm || 0
          systemState.motorStates[motorName].direction = data.command.direction || 'CW'
          systemState.motorStates[motorName].last_update = data.timestamp || Date.now()/1000
          console.log(`Updated ${motorName} state: ${data.command.velocity_rpm} RPM ${data.command.direction}`)
        }
      }
      break
    
    case 'blockchain_data_update':
      // Update blockchain data for visualization
      systemState.blockchainData = data.blockchain_data
      console.log('Received blockchain data update:', data.blockchain_data)
      break
    
    
    case 'mode_changed':
      console.log('Mode changed to:', data.new_mode)
      systemState.mode = data.new_mode
      break
    
    case 'error':
      console.error('Server error:', data.message)
      alert(`Error: ${data.message}`)
      break
    
    default:
      console.log('Received unhandled message:', data)
  }
}

// Send message to server
const sendMessage = (message: any) => {
  if (ws.value?.readyState === WebSocket.OPEN) {
    console.log('Sending message:', message)
    ws.value.send(JSON.stringify(message))
  } else {
    console.error('WebSocket not connected, cannot send:', message)
  }
}

// Motor control functions
const sendMotorCommand = (motorName: string, velocityRpm: number, direction: string) => {
  sendMessage({
    type: 'motor_command',
    motor_name: motorName,
    velocity_rpm: velocityRpm,
    direction: direction,
    source: 'manual'
  })
}


const changeMode = (newMode: string) => {
  // Prevent unnecessary mode changes
  if (newMode === systemState.mode) {
    console.log(`Mode change ignored - already in ${newMode} mode`)
    return
  }
  
  // Debounce rapid mode changes (prevent loops)
  const now = Date.now()
  if (now - lastModeChangeTime < 2000) {
    console.log(`Mode change ignored - too recent (${now - lastModeChangeTime}ms ago)`)
    return
  }
  lastModeChangeTime = now
  
  console.log(`User initiated mode change: ${systemState.mode} → ${newMode}`)
  
  // Send mode change
  sendMessage({
    type: 'mode_change',
    mode: newMode
  })
  
  // CRITICAL: When switching to manual mode, request last motor states and send as manual commands
  // This ensures smooth transition with actual motor positions from auto mode
  if (newMode === 'manual') {
    console.log('Switching to manual - requesting last motor states for smooth transition')
    
    // Request last motor states from server
    sendMessage({
      type: 'get_last_motor_states'
    })
    
    // The server will respond with last states, then we'll send them as manual commands
    // If no response, use current states as fallback after delay
    setTimeout(() => {
      // Fallback: Send current motor states if we haven't received updates
      if (Object.values(systemState.motorStates).every((state: any) => state.velocity_rpm === 0)) {
        console.log('No motor states received, using defaults')
        // Set some default values to establish manual control
        const defaultMotorStates = {
          motor_canvas: { velocity_rpm: 10, direction: 'CW' },
          motor_pb: { velocity_rpm: 5, direction: 'CW' },
          motor_pcd: { velocity_rpm: 5, direction: 'CW' },
          motor_pe: { velocity_rpm: 5, direction: 'CW' }
        }
        
        Object.entries(defaultMotorStates).forEach(([motorName, state]) => {
          console.log(`Sending default manual command for ${motorName}: ${state.velocity_rpm} RPM ${state.direction}`)
          sendMessage({
            type: 'motor_command',
            motor_name: motorName,
            velocity_rpm: state.velocity_rpm,
            direction: state.direction,
            source: 'manual'
          })
        })
      } else {
        // Use actual motor states if available
        Object.entries(systemState.motorStates).forEach(([motorName, state]: [string, any]) => {
          const velocity = state?.velocity_rpm || 10
          const direction = state?.direction || 'CW'
          
          console.log(`Sending manual command for ${motorName}: ${velocity} RPM ${direction}`)
          sendMessage({
            type: 'motor_command',
            motor_name: motorName,
            velocity_rpm: velocity,
            direction: direction,
            source: 'manual'
          })
        })
      }
    }, 1000)
  }
}


// Helper functions for display
const getMotorDisplayName = (motorName: string) => {
  const nameMap: Record<string, string> = {
    'motor_canvas': 'Canvas',
    'motor_pb': 'PB',
    'motor_pcd': 'PCD', 
    'motor_pe': 'PE'
  }
  return nameMap[motorName] || motorName
}

const getLastUpdateText = (state: any) => {
  if (!state?.last_update) return 'Never'
  const seconds = Math.floor((Date.now() / 1000) - state.last_update)
  return seconds < 60 ? `${seconds}s ago` : `${Math.floor(seconds / 60)}m ago`
}

// Lifecycle
onMounted(() => {
  connect()
})

onUnmounted(() => {
  disconnect()
})
</script>

<template>
  <div class="manual-control">
    <header class="control-header">
      <h1>Drawing Machine Manual Control</h1>
      
      <!-- Connection Status -->
      <div class="connection-status">
        <div class="status-indicator" :class="connectionStatus">
          <div class="status-dot"></div>
          <span>{{ connectionStatus.toUpperCase() }}</span>
        </div>
        
        <div class="connection-controls">
          <input 
            v-model="wsUrl" 
            placeholder="WebSocket URL"
            :disabled="connectionStatus === 'connected'"
          />
          <input 
            v-model="apiKey" 
            placeholder="API Key (optional - for blockchain data)"
            type="password"
            :disabled="connectionStatus === 'connected'"
          />
          <button @click="connect" :disabled="connectionStatus === 'connected'">
            Connect
          </button>
          <button @click="disconnect" :disabled="connectionStatus !== 'connected'">
            Disconnect
          </button>
        </div>
      </div>
    </header>

    <div v-if="connectionStatus === 'connected'" class="control-panel">
      <!-- Simple Mode Buttons (More Reliable) -->
      <div class="simple-mode-selector">
        <h2>Control Mode</h2>
        <div class="mode-buttons">
          <button 
            class="mode-btn"
            :class="{ active: systemState.mode === 'manual' }"
            @click.stop.prevent="changeMode('manual')"
          >
            🎮 Manual Control
          </button>
          <button 
            class="mode-btn"
            :class="{ active: systemState.mode === 'auto' }"
            @click.stop.prevent="changeMode('auto')"
          >
            ⛓️ Auto Blockchain
          </button>
        </div>
        <p class="current-mode">Current Mode: <strong>{{ systemState.mode?.toUpperCase() || 'UNKNOWN' }}</strong></p>
      </div>
      
      <!-- Real-time Motor Visualization -->
      <MotorVisualization
        :motor-states="systemState.motorStates"
        :blockchain-data="systemState.blockchainData"
        :is-active="connectionStatus === 'connected'"
      />

      <!-- Motor Controls (Only visible in manual mode) -->
      <div v-if="systemState.mode === 'manual'" class="motors-section">
        <h2>Motor Controls</h2>
        <div class="motors-grid">
          <MotorControl
            v-for="(state, motorName) in systemState.motorStates"
            :key="motorName"
            :motor-name="motorName"
            :motor-state="state"
            :safety-limit="100"
            :disabled="false"
            @motor-command="sendMotorCommand"
          />
        </div>
      </div>

      <!-- Auto Mode Display (Only visible in auto mode) -->
      <div v-else-if="systemState.mode === 'auto'" class="auto-mode-section">
        <h2>🔗 Auto-Blockchain Mode Active</h2>
        <p class="auto-description">
          Motors are being controlled automatically by live blockchain data. 
          Switch to Manual mode to take direct control.
        </p>
        
        <!-- Motor Status Display (read-only) -->
        <div class="motor-status-grid">
          <div 
            v-for="(state, motorName) in systemState.motorStates"
            :key="motorName"
            class="motor-status-card"
          >
            <h4>{{ getMotorDisplayName(motorName) }}</h4>
            <div class="status-value">
              <span class="rpm-display">{{ 
                state?.direction === 'CCW' 
                  ? '-' + (state?.velocity_rpm?.toFixed(1) || '0')
                  : (state?.velocity_rpm?.toFixed(1) || '0')
              }}</span>
              <span class="rpm-unit">RPM</span>
            </div>
            <div class="last-update">{{ getLastUpdateText(state) }}</div>
          </div>
        </div>
      </div>

    </div>

    <div v-else class="connecting-message">
      <p v-if="connectionStatus === 'connecting'">Connecting to manual control server...</p>
      <p v-else>Not connected to manual control server. Click Connect to start.</p>
    </div>
  </div>
</template>

<style scoped>
.manual-control {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.control-header {
  text-align: center;
  margin-bottom: 30px;
}

.control-header h1 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.connection-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 20px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  transition: background-color 0.3s;
}

.status-indicator.connected .status-dot {
  background-color: #27ae60;
}

.status-indicator.connecting .status-dot {
  background-color: #f39c12;
  animation: pulse 1s infinite;
}

.status-indicator.disconnected .status-dot {
  background-color: #e74c3c;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.connection-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.connection-controls input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  width: 200px;
}

.connection-controls button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: #3498db;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s;
}

.connection-controls button:hover:not(:disabled) {
  background: #2980b9;
}

.connection-controls button:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.control-panel {
  display: flex;
  flex-direction: column;
  gap: 30px;
}


.motors-section h2 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.motors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.connecting-message {
  text-align: center;
  padding: 40px;
  color: #7f8c8d;
  font-size: 18px;
}

.simple-mode-selector {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.simple-mode-selector h2 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #2c3e50;
}

.mode-buttons {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.mode-btn {
  flex: 1;
  padding: 12px 20px;
  border: 2px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.3s;
}

.mode-btn:hover {
  background: #f8f9fa;
  border-color: #3498db;
}

.mode-btn.active {
  background: #3498db;
  color: white;
  border-color: #3498db;
}

.mode-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.current-mode {
  text-align: center;
  color: #6c757d;
  margin: 0;
}

.current-mode strong {
  color: #2c3e50;
}

.auto-mode-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 30px;
  color: white;
  text-align: center;
  margin-bottom: 30px;
}

.auto-mode-section h2 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 24px;
}

.auto-description {
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 25px;
  line-height: 1.5;
}

.motor-status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-top: 20px;
}

.motor-status-card {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  padding: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.motor-status-card h4 {
  margin: 0 0 10px 0;
  font-size: 16px;
  font-weight: bold;
}

.status-value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8px;
  margin-bottom: 8px;
}

.rpm-display {
  font-size: 20px;
  font-weight: bold;
  font-family: 'Courier New', monospace;
}

.rpm-unit {
  font-size: 12px;
  opacity: 0.8;
}

.last-update {
  font-size: 12px;
  opacity: 0.7;
}


@media (max-width: 768px) {
  .connection-status {
    flex-direction: column;
    gap: 15px;
  }
  
  .connection-controls {
    flex-direction: column;
    width: 100%;
  }
  
  .connection-controls input {
    width: 100%;
  }
  
  .motors-grid {
    grid-template-columns: 1fr;
  }
  
  .mode-buttons {
    flex-direction: column;
  }
}
</style>