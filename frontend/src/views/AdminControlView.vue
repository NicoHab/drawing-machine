<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import MotorControl from '../components/MotorControl.vue'
import MotorVisualization from '../components/MotorVisualization.vue'
import ModeSelector from '../components/ModeSelector.vue'
import DataDisplayPanel from '../components/DataDisplayPanel.vue'

// WebSocket connection
const ws = ref<WebSocket | null>(null)
const connectionStatus = ref<'disconnected' | 'connecting' | 'connected'>('disconnected')

// System state
const systemState = reactive({
  mode: 'manual',
  motorStates: {
    motor_canvas: { velocity_rpm: 0, direction: 'CW', last_update: Date.now() / 1000, is_enabled: true },
    motor_pb: { velocity_rpm: 0, direction: 'CW', last_update: Date.now() / 1000, is_enabled: true },
    motor_pcd: { velocity_rpm: 0, direction: 'CW', last_update: Date.now() / 1000, is_enabled: true },
    motor_pe: { velocity_rpm: 0, direction: 'CW', last_update: Date.now() / 1000, is_enabled: true }
  } as Record<string, any>,
  blockchainData: {
    eth_price_usd: 0,
    gas_price_gwei: 0,
    base_fee_gwei: 0,
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

// Debug tracking
const lastMessageReceived = ref<any>(null)
const messagesReceived = ref(0)

// Connect to WebSocket server
const connect = () => {
  if (ws.value?.readyState === WebSocket.OPEN) {
    return
  }

  connectionStatus.value = 'connecting'
  ws.value = new WebSocket(wsUrl.value)

  ws.value.onopen = () => {
    connectionStatus.value = 'connected'

    // Send authentication
    const authMessage = {
      type: 'authenticate',
      client_type: 'web_ui',
      user_info: {},
      api_key: apiKey.value
    }
    ws.value?.send(JSON.stringify(authMessage))
  }

  ws.value.onmessage = (event) => {
    handleMessage(JSON.parse(event.data))
  }

  ws.value.onclose = () => {
    connectionStatus.value = 'disconnected'
    setTimeout(connect, 3000) // Auto-reconnect
  }

  ws.value.onerror = (error) => {
    console.error('WebSocket error:', error)
    connectionStatus.value = 'disconnected'
  }
}

// Handle incoming messages
const handleMessage = (data: any) => {

  // Update debug tracking
  messagesReceived.value++
  lastMessageReceived.value = {
    type: data.type,
    timestamp: new Date().toLocaleTimeString(),
    hasMotorCommands: !!data.motor_commands,
    motorCommandsCount: data.motor_commands ? Object.keys(data.motor_commands).length : 0
  }

  switch (data.type) {
    case 'authenticated':
      if (data.api_access === false) {
        alert('Demo mode: Blockchain API disabled. Enter API key to enable live data.')
      }
      break

    case 'system_state':
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
      if (data.new_mode) {
        systemState.mode = data.new_mode
      }
      break

    case 'blockchain_data':
    case 'blockchain_data_update':
      const incomingData = data.blockchain_data || data.data

      if (data.blockchain_data) {
        Object.assign(systemState.blockchainData, data.blockchain_data)
      } else if (data.data) {
        Object.assign(systemState.blockchainData, data.data)
      }


      // Check if motor commands are included in blockchain update
      if (data.motor_commands) {

        // Apply motor commands to update motor states
        Object.keys(data.motor_commands).forEach(motorName => {
          const motorCommand = data.motor_commands[motorName]
          if (systemState.motorStates[motorName] && motorCommand) {

            // Update motor state with new command
            const oldRpm = systemState.motorStates[motorName].velocity_rpm
            Object.assign(systemState.motorStates[motorName], {
              velocity_rpm: motorCommand.velocity_rpm || 0,
              direction: motorCommand.direction || 'CW',
              last_update: Date.now() / 1000,
              is_enabled: true
            })
          }
        })
      }
      break

    case 'motor_state_update':
    case 'motor_update':
      const oldState = systemState.motorStates[data.motor_name] ? { ...systemState.motorStates[data.motor_name] } : null
      if (systemState.motorStates[data.motor_name]) {
        Object.assign(systemState.motorStates[data.motor_name], data.state)
      } else {
        // Create new motor state if it doesn't exist
        systemState.motorStates[data.motor_name] = data.state
      }
      break

    case 'motor_command_executed':
      break
  }
}

// Motor control functions
const sendMotorCommand = (motorName: string, velocity: number, direction: string) => {
  if (ws.value?.readyState === WebSocket.OPEN) {
    const command = {
      type: 'motor_command',
      motor_name: motorName,
      velocity_rpm: velocity,
      direction: direction
    }
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
  if (ws.value?.readyState === WebSocket.OPEN) {
    lastModeChangeTime = Date.now()
    const command = {
      type: 'mode_change',
      mode: newMode
    }
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
            <div class="w-3 h-3 rounded-full transition-colors duration-300" :class="{
              'bg-red-500': connectionStatus === 'disconnected',
              'bg-yellow-500 animate-pulse': connectionStatus === 'connecting',
              'bg-green-500': connectionStatus === 'connected'
            }"></div>
            <span class="text-sm font-medium" :class="{
              'text-red-400': connectionStatus === 'disconnected',
              'text-yellow-400': connectionStatus === 'connecting',
              'text-green-400': connectionStatus === 'connected'
            }">
              {{ connectionStatus === 'connected' ? 'Active' : 'Inactive' }}
            </span>
          </div>
        </div>
      </div>

    </header>

    <!-- Main Content -->
    <main class="container mx-auto px-6 pb-8">
      <!-- Controls Section -->
      <div class="space-y-6 mb-8">
        <!-- Mode Selector -->
        <div class="bg-gray-800/30 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
          <h2 class="text-2xl font-bold mb-4">System Control</h2>
          <ModeSelector :current-mode="systemState.mode" @modeChange="switchMode" />

          <!-- API Key Input -->
          <div class="mt-4">
            <label class="block text-sm font-medium text-gray-300 mb-2">
              API Key
              <span v-if="apiKey" class="text-green-400 text-xs">(✓ Set)</span>
              <span v-else class="text-gray-400 text-xs">(Demo mode)</span>
            </label>
            <input v-model="apiKey" type="password" placeholder="Enter API key for live blockchain data"
              class="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
              @input="onApiKeyChange" />
          </div>
        </div>

        <!-- Motor Controls - Only show in manual mode -->
        <div v-if="systemState.mode === 'manual'"
          class="bg-gray-800/30 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-2xl font-bold">Manual Motor Control</h2>
            <button @click="emergencyStop"
              class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-colors">
              Emergency Stop
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MotorControl v-for="(state, motorName) in systemState.motorStates" :key="motorName"
              :motor-name="motorName as string" :motor-state="state" :safety-limit="50"
              :disabled="connectionStatus !== 'connected'" @motorCommand="sendMotorCommand" />
          </div>
        </div>
      </div>

      <!-- Visualization and Data Section -->
      <div class="gap-6">

        <!-- Motor Visualization - Always on top -->
        <div class="w-full space-y-6">
          <MotorVisualization :motor-states="systemState.motorStates" :is-active="connectionStatus === 'connected'"
            :blockchain-data="systemState.blockchainData" />
        </div>

        <!-- Data Display - Always below -->
        <div class="w-full space-y-6">
          <DataDisplayPanel :system-state="systemState" :is-read-only="false" />
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* Custom component styles */
</style>