<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import MotorControl from '../components/MotorControl.vue'
import MotorVisualization from '../components/MotorVisualization.vue'
import ModeSelector from '../components/ModeSelector.vue'

// WebSocket connection
const ws = ref<WebSocket | null>(null)
const connectionStatus = ref<'disconnected' | 'connecting' | 'connected'>('disconnected')

// System state
const systemState = reactive({
  mode: 'manual',
  motorStates: {
    motor_canvas: { velocity_rpm: 0, direction: 'CW', last_update: Date.now()/1000, is_enabled: true },
    motor_pb: { velocity_rpm: 0, direction: 'CW', last_update: Date.now()/1000, is_enabled: true },
    motor_pcd: { velocity_rpm: 0, direction: 'CW', last_update: Date.now()/1000, is_enabled: true },
    motor_pe: { velocity_rpm: 0, direction: 'CW', last_update: Date.now()/1000, is_enabled: true }
  } as Record<string, any>,
  blockchainData: {
    eth_price_usd: 0,
    gas_price_gwei: 0,
    block_number: 'Loading...',
    block_fullness_percent: 0,
    blob_space_utilization_percent: 0,
    epoch: 'N/A',
    data_sources: {}
  }
})

// Connection settings
const wsUrl = ref(import.meta.env.VITE_BACKEND_URL || 'wss://drawing-machine-production.up.railway.app')
const apiKey = ref('')
let lastModeChangeTime = 0

// Connect to WebSocket server
const connect = () => {
  if (ws.value?.readyState === WebSocket.OPEN) {
    return
  }

  console.log('Connecting to WebSocket at:', wsUrl.value)
  connectionStatus.value = 'connecting'
  ws.value = new WebSocket(wsUrl.value)

  ws.value.onopen = () => {
    connectionStatus.value = 'connected'
    console.log(`Connected to server at ${wsUrl.value}`)
    
    // Send authentication
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
    console.log('Disconnected from server')
    setTimeout(connect, 3000) // Auto-reconnect
  }

  ws.value.onerror = (error) => {
    console.error('WebSocket error:', error)
    connectionStatus.value = 'disconnected'
  }
}

// Handle incoming messages
const handleMessage = (data: any) => {
  console.log(`Received message type: ${data.type}`, data)
  
  switch (data.type) {
    case 'authenticated':
      console.log('Successfully authenticated:', data.message)
      console.log('Authentication response:', data)
      if (data.api_access === false) {
        console.log('API access denied - in demo mode')
        alert('Demo mode: Blockchain API disabled. Enter API key to enable live data.')
      } else {
        console.log('API access granted - live blockchain data enabled')
      }
      break
      
    case 'system_state':
      console.log('Updating system state:', data)
      const now = Date.now()
      if (now - lastModeChangeTime > 2000) {
        systemState.mode = data.mode
        if (data.motor_states) {
          // Merge motor states instead of replacing
          Object.keys(data.motor_states).forEach(motorName => {
            if (systemState.motorStates[motorName]) {
              Object.assign(systemState.motorStates[motorName], data.motor_states[motorName])
            } else {
              systemState.motorStates[motorName] = data.motor_states[motorName]
            }
          })
        }
      }
      break
      
    case 'mode_changed':
      console.log('Mode changed:', data)
      if (data.new_mode) {
        systemState.mode = data.new_mode
        console.log('Updated system mode to:', systemState.mode)
      }
      break
      
    case 'blockchain_data':
    case 'blockchain_data_update':
      console.log('Blockchain data received:', data)
      if (data.blockchain_data) {
        Object.assign(systemState.blockchainData, data.blockchain_data)
      } else if (data.data) {
        Object.assign(systemState.blockchainData, data.data)
      }
      
      // Debug blob utilization specifically for motor_pcd
      console.log('Blob utilization for motor_pcd:', systemState.blockchainData.blob_space_utilization_percent)
      
      // Check if motor commands are included in blockchain update
      if (data.motor_commands) {
        console.log('Motor commands from blockchain:', data.motor_commands)
        if (data.motor_commands.motor_pcd) {
          console.log('motor_pcd command:', data.motor_commands.motor_pcd)
        } else {
          console.log('No motor_pcd command in blockchain update')
        }
      }
      break
      
    case 'motor_state_update':
    case 'motor_update':
      console.log('Motor update received:', data)
      const oldState = systemState.motorStates[data.motor_name] ? {...systemState.motorStates[data.motor_name]} : null
      if (systemState.motorStates[data.motor_name]) {
        Object.assign(systemState.motorStates[data.motor_name], data.state)
      } else {
        // Create new motor state if it doesn't exist
        systemState.motorStates[data.motor_name] = data.state
      }
      console.log('Motor state updated:', {
        motor: data.motor_name,
        oldState,
        newState: systemState.motorStates[data.motor_name]
      })
      break
      
    case 'motor_command_executed':
      console.log('Motor command executed:', data)
      break
  }
}

// Motor control functions
const sendMotorCommand = (motorName: string, velocity: number, direction: string) => {
  console.log('Sending motor command:', { motorName, velocity, direction })
  if (ws.value?.readyState === WebSocket.OPEN) {
    const command = {
      type: 'motor_command',
      motor_name: motorName,
      velocity_rpm: velocity,
      direction: direction
    }
    console.log('WebSocket command:', command)
    ws.value.send(JSON.stringify(command))
  } else {
    console.error('WebSocket not connected, status:', connectionStatus.value)
  }
}

const emergencyStop = () => {
  if (ws.value?.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({
      type: 'emergency_stop'
    }))
  }
}

const switchMode = (newMode: string) => {
  console.log('Switching mode to:', newMode)
  if (ws.value?.readyState === WebSocket.OPEN) {
    lastModeChangeTime = Date.now()
    const command = {
      type: 'mode_change',
      mode: newMode
    }
    console.log('Sending mode change command:', command)
    ws.value.send(JSON.stringify(command))
  } else {
    console.error('Cannot switch mode - WebSocket not connected')
  }
}

// API key change handler
const onApiKeyChange = () => {
  // Re-authenticate with new API key
  if (ws.value?.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify({
      type: 'authenticate',
      client_type: 'web_ui',
      user_info: {},
      api_key: apiKey.value
    }))
  }
}


onMounted(() => {
  connect()
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white">
    <!-- Header -->
    <header class="container mx-auto px-6 py-8">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          Drawing Machine
        </h1>
        
        <!-- Connection Status -->
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <div 
              class="w-3 h-3 rounded-full transition-colors duration-300"
              :class="{
                'bg-red-500': connectionStatus === 'disconnected',
                'bg-yellow-500 animate-pulse': connectionStatus === 'connecting',
                'bg-green-500': connectionStatus === 'connected'
              }"
            ></div>
            <span 
              class="text-sm font-medium capitalize"
              :class="{
                'text-red-400': connectionStatus === 'disconnected',
                'text-yellow-400': connectionStatus === 'connecting',
                'text-green-400': connectionStatus === 'connected'
              }"
            >
              {{ connectionStatus }}
            </span>
          </div>
        </div>
      </div>

    </header>

    <!-- Main Content -->
    <main class="container mx-auto px-6 pb-8">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        <!-- Left Column: Controls -->
        <div class="space-y-6">
          <!-- Mode Selector -->
          <div class="bg-gray-800/30 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h2 class="text-2xl font-bold mb-4">System Control</h2>
            <ModeSelector 
              :current-mode="systemState.mode" 
              @modeChange="switchMode"
            />
            
            <!-- API Key Input -->
            <div class="mt-4">
              <label class="block text-sm font-medium text-gray-300 mb-2">
                API Key 
                <span v-if="apiKey" class="text-green-400 text-xs">(✓ Set)</span>
                <span v-else class="text-gray-400 text-xs">(Demo mode)</span>
              </label>
              <input 
                v-model="apiKey" 
                type="password" 
                placeholder="Enter API key for live blockchain data"
                class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                @input="onApiKeyChange"
              />
            </div>
          </div>

          <!-- Motor Controls - Only show in manual mode -->
          <div v-if="systemState.mode === 'manual'" class="bg-gray-800/30 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <div class="flex justify-between items-center mb-4">
              <h2 class="text-2xl font-bold">Manual Motor Control</h2>
              <button 
                @click="emergencyStop"
                class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-colors"
              >
                Emergency Stop
              </button>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <MotorControl
                v-for="(state, motorName) in systemState.motorStates"
                :key="motorName"
                :motor-name="motorName as string"
                :motor-state="state"
                :safety-limit="50"
                :disabled="connectionStatus !== 'connected'"
                @motorCommand="sendMotorCommand"
              />
            </div>
          </div>

          <!-- Blockchain Auto Status - Only show in auto mode -->
          <div v-if="systemState.mode === 'auto'" class="bg-gray-800/30 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h2 class="text-2xl font-bold mb-4">Blockchain Auto Mode</h2>
            
            <!-- Block & Epoch Info at Top -->
            <div class="grid grid-cols-2 gap-4 mb-6">
              <div class="bg-gray-900/50 rounded-lg p-4">
                <h3 class="text-sm font-semibold text-white mb-1">Current Block</h3>
                <p class="text-2xl font-bold">
                  {{ systemState.blockchainData.block_number || 'Loading...' }}
                </p>
              </div>
              
              <div class="bg-gray-900/50 rounded-lg p-4">
                <h3 class="text-sm font-semibold text-white mb-1">Current Epoch</h3>
                <p class="text-2xl font-bold">
                  {{ systemState.blockchainData.epoch || 'N/A' }}
                </p>
              </div>
            </div>

            <!-- Main Blockchain Data -->
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div class="bg-gray-900/50 rounded-lg p-4">
                <h3 class="text-sm font-semibold text-blue-400 mb-1">ETH Price</h3>
                <p class="text-2xl font-bold">
                  ${{ systemState.blockchainData.eth_price_usd?.toFixed(4) || '0.0000' }}
                </p>
              </div>
              
              <div class="bg-gray-900/50 rounded-lg p-4">
                <h3 class="text-sm font-semibold text-green-400 mb-1">Gas Price</h3>
                <p class="text-2xl font-bold">
                  {{ systemState.blockchainData.gas_price_gwei?.toFixed(2) || '0.00' }} <span class="text-sm text-gray-400">gwei</span>
                </p>
              </div>
              
              <div class="bg-gray-900/50 rounded-lg p-4">
                <h3 class="text-sm font-semibold text-orange-400 mb-1">Block Utilization</h3>
                <p class="text-2xl font-bold">
                  {{ systemState.blockchainData.block_fullness_percent?.toFixed(2) || '0.00' }}<span class="text-sm text-gray-400">%</span>
                </p>
              </div>
              
              <div class="bg-gray-900/50 rounded-lg p-4">
                <h3 class="text-sm font-semibold text-purple-400 mb-1">Blob Utilization</h3>
                <p class="text-2xl font-bold">
                  {{ systemState.blockchainData.blob_space_utilization_percent?.toFixed(2) || '0.00' }}<span class="text-sm text-gray-400">%</span>
                </p>
              </div>
            </div>
            
            <div class="mt-4 text-sm text-gray-400">
              Motors are automatically controlled by live Ethereum blockchain data
            </div>
          </div>

        </div>

        <!-- Right Column: Visualization & Status -->
        <div class="space-y-6">
          <!-- Motor Visualization -->
          <div class="bg-gray-800/30 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h2 class="text-2xl font-bold mb-4">Motor Status</h2>
            <MotorVisualization 
              :motor-states="systemState.motorStates" 
              :is-active="connectionStatus === 'connected'"
              :blockchain-data="systemState.blockchainData"
            />
          </div>

          <!-- System Status -->
          <div class="bg-gray-800/30 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h2 class="text-2xl font-bold mb-4">System Status</h2>
            
            <div class="space-y-3">
              <!-- Current Mode -->
              <div class="flex justify-between items-center p-3 bg-gray-900/50 rounded-lg">
                <span class="font-medium">Current Mode</span>
                <span class="capitalize font-semibold" :class="systemState.mode === 'auto' ? 'text-green-400' : 'text-blue-400'">
                  {{ systemState.mode === 'auto' ? 'Blockchain Auto' : 'Manual Control' }}
                </span>
              </div>

              <!-- Motor Count -->
              <div class="flex justify-between items-center p-3 bg-gray-900/50 rounded-lg">
                <span class="font-medium">Active Motors</span>
                <span class="font-semibold text-purple-400">
                  {{ Object.keys(systemState.motorStates).length }}
                </span>
              </div>

              <!-- Data Sources -->
              <div class="flex justify-between items-center p-3 bg-gray-900/50 rounded-lg">
                <span class="font-medium">Blockchain Data</span>
                <span class="font-semibold" :class="(systemState.blockchainData.eth_price_usd > 0 && systemState.mode === 'auto') ? 'text-green-400' : 'text-gray-400'">
                  {{ (systemState.blockchainData.eth_price_usd > 0 && systemState.mode === 'auto') ? 'Live & Active' : 'Standby' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Debug Info -->
          <div class="bg-gray-800/30 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
            <h3 class="text-lg font-bold mb-3">Debug Info</h3>
            <div class="text-xs text-gray-300 font-mono space-y-1">
              <div>WebSocket URL: {{ wsUrl }}</div>
              <div>Connection: {{ connectionStatus }}</div>
              <div>Motor Count: {{ Object.keys(systemState.motorStates).length }}</div>
              <div>Mode: {{ systemState.mode }}</div>
              <div class="mt-2 text-yellow-400">Motor States:</div>
              <div v-for="(state, motorName) in systemState.motorStates" :key="motorName" class="ml-2">
                {{ motorName }}: {{ state.velocity_rpm?.toFixed(1) || 0 }}rpm {{ state.direction || 'CW' }} 
                {{ state.is_enabled ? '✓' : '✗' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* Custom component styles if needed */
</style>