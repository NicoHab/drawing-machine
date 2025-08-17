<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import MotorControl from '../components/MotorControl.vue'
import SessionRecorder from '../components/SessionRecorder.vue'
import ModeSelector from '../components/ModeSelector.vue'

// WebSocket connection
const ws = ref<WebSocket | null>(null)
const connectionStatus = ref<'disconnected' | 'connecting' | 'connected'>('disconnected')

// System state
const systemState = reactive({
  mode: 'manual',
  emergencyStopped: false,
  motorStates: {} as Record<string, any>,
  safetyLimits: {} as Record<string, number>,
  recordingActive: false
})

// Connection settings - use environment variable with fallback
const wsUrl = ref(import.meta.env.VITE_WEBSOCKET_URL || 'ws://localhost:8766')

// Connect to WebSocket server
const connect = () => {
  if (ws.value?.readyState === WebSocket.OPEN) {
    return
  }

  connectionStatus.value = 'connecting'
  ws.value = new WebSocket(wsUrl.value)

  ws.value.onopen = () => {
    connectionStatus.value = 'connected'
    console.log('Connected to manual control server')
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
  switch (data.type) {
    case 'system_state':
      Object.assign(systemState, {
        mode: data.mode,
        emergencyStopped: data.emergency_stopped,
        motorStates: data.motor_states,
        safetyLimits: data.safety_limits,
        recordingActive: data.recording_active
      })
      break
    
    case 'motor_update':
      systemState.motorStates[data.motor_name] = data.state
      break
    
    case 'emergency_stop':
      systemState.emergencyStopped = true
      alert('EMERGENCY STOP ACTIVATED')
      break
    
    case 'mode_changed':
      systemState.mode = data.new_mode
      break
    
    case 'error':
      console.error('Server error:', data.message)
      alert(`Error: ${data.message}`)
      break
    
    default:
      console.log('Received message:', data)
  }
}

// Send message to server
const sendMessage = (message: any) => {
  if (ws.value?.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify(message))
  } else {
    console.error('WebSocket not connected')
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

const emergencyStop = () => {
  sendMessage({ type: 'emergency_stop' })
}

const changeMode = (newMode: string) => {
  sendMessage({
    type: 'mode_change',
    mode: newMode
  })
}

// Session recording functions
const startRecording = (sessionName: string) => {
  sendMessage({
    type: 'start_recording',
    session_name: sessionName
  })
}

const stopRecording = () => {
  sendMessage({ type: 'stop_recording' })
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
      <!-- Mode Selector -->
      <ModeSelector 
        :current-mode="systemState.mode"
        @mode-change="changeMode"
      />

      <!-- Emergency Stop -->
      <div class="emergency-section">
        <button 
          class="emergency-stop"
          :class="{ active: systemState.emergencyStopped }"
          @click="emergencyStop"
        >
          🛑 EMERGENCY STOP
        </button>
        <p v-if="systemState.emergencyStopped" class="emergency-message">
          System in emergency stop state. Change mode to reset.
        </p>
      </div>

      <!-- Motor Controls -->
      <div class="motors-section">
        <h2>Motor Controls</h2>
        <div class="motors-grid">
          <MotorControl
            v-for="(state, motorName) in systemState.motorStates"
            :key="motorName"
            :motor-name="motorName"
            :motor-state="state"
            :safety-limit="systemState.safetyLimits[motorName.replace('motor_', '') + '_max'] || 100"
            :disabled="systemState.emergencyStopped"
            @motor-command="sendMotorCommand"
          />
        </div>
      </div>

      <!-- Session Recording -->
      <SessionRecorder
        :recording-active="systemState.recordingActive"
        @start-recording="startRecording"
        @stop-recording="stopRecording"
        @send-message="sendMessage"
      />
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

.emergency-section {
  text-align: center;
}

.emergency-stop {
  font-size: 18px;
  font-weight: bold;
  padding: 15px 30px;
  border: none;
  border-radius: 8px;
  background: #e74c3c;
  color: white;
  cursor: pointer;
  transition: all 0.3s;
}

.emergency-stop:hover {
  background: #c0392b;
  transform: scale(1.05);
}

.emergency-stop.active {
  background: #8e44ad;
  animation: flash 1s infinite;
}

@keyframes flash {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.emergency-message {
  color: #e74c3c;
  font-weight: bold;
  margin-top: 10px;
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
}
</style>