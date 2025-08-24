<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import MotorVisualization from '../components/MotorVisualization.vue'
import DataDisplayPanel from '../components/DataDisplayPanel.vue'

// Connection settings (read-only connection)
const wsUrl = ref(import.meta.env.VITE_BACKEND_URL || 'wss://drawing-machine-production.up.railway.app')

// WebSocket connection
const ws = ref<WebSocket | null>(null)
const connectionStatus = ref<'disconnected' | 'connecting' | 'connected'>('disconnected')

// System state (read-only)
const systemState = reactive({
  mode: 'auto',
  blockchainData: {
    eth_price_usd: 0,
    gas_price_gwei: 0,
    base_fee_gwei: 0,
    blob_space_utilization_percent: 0,
    block_fullness_percent: 0,
    block_number: 0,
    epoch: 0
  },
  motorStates: {
    motor_canvas: { velocity_rpm: 0, direction: 'CW', last_update: Date.now() / 1000, is_enabled: true },
    motor_pb: { velocity_rpm: 0, direction: 'CW', last_update: Date.now() / 1000, is_enabled: true },
    motor_pcd: { velocity_rpm: 0, direction: 'CW', last_update: Date.now() / 1000, is_enabled: true },
    motor_pe: { velocity_rpm: 0, direction: 'CW', last_update: Date.now() / 1000, is_enabled: true }
  } as Record<string, any>
})

// Connect to WebSocket (read-only, no authentication)
const connectToServer = () => {
  console.log('Visitor connecting to:', wsUrl.value)

  ws.value = new WebSocket(wsUrl.value)

  ws.value.onopen = () => {
    console.log('Visitor connected to server')
    connectionStatus.value = 'connected'

    // Send authentication message (visitor mode, no API key)
    if (ws.value) {
      ws.value.send(JSON.stringify({
        type: 'authenticate',
        client_type: 'visitor',
        user_info: {},
        api_key: '' // No API key for visitors
      }))
    }
  }

  ws.value.onclose = () => {
    console.log('Visitor disconnected from server')
    connectionStatus.value = 'disconnected'
    // Auto-reconnect for visitors
    setTimeout(connectToServer, 5000)
  }

  ws.value.onerror = (error) => {
    console.error('Visitor WebSocket error:', error)
    connectionStatus.value = 'disconnected'
  }

  ws.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleMessage(data)
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }
}

// Handle incoming messages (read-only)
const handleMessage = (data: any) => {
  console.log('Visitor received message:', data.type)

  // Debug: Log ALL WebSocket message data for blockchain updates
  if (data.type === 'blockchain_data' || data.type === 'blockchain_data_update') {
    console.log('🚨 RAW WEBSOCKET MESSAGE:', JSON.stringify(data, null, 2))
  }

  switch (data.type) {
    case 'authenticated':
      console.log('Visitor authenticated:', data)
      console.log('Connection status after auth:', connectionStatus.value)
      break

    case 'authentication_failed':
      console.error('Visitor authentication failed:', data)
      // For visitors, authentication failure shouldn't happen now, but handle gracefully
      connectionStatus.value = 'disconnected'
      console.log('Connection status after auth failure:', connectionStatus.value)
      break

    case 'system_state':
      console.log('Visitor - Updating system state:', data)
      if (data.mode) {
        systemState.mode = data.mode
      }
      if (data.motor_states) {
        // Merge motor states instead of replacing (like AdminControlView)
        Object.keys(data.motor_states).forEach(motorName => {
          if (systemState.motorStates[motorName]) {
            Object.assign(systemState.motorStates[motorName], data.motor_states[motorName])
          } else {
            systemState.motorStates[motorName] = data.motor_states[motorName]
          }
        })
      }
      break

    case 'mode_changed':
      console.log('Visitor - Mode changed:', data)
      if (data.new_mode) {
        systemState.mode = data.new_mode
        console.log('Visitor - Updated system mode to:', systemState.mode)
      }
      break

    case 'blockchain_data':
    case 'blockchain_data_update':
      // Debug: Log what base_fee_gwei we're receiving
      console.log('🚨 VISITOR RAW WEBSOCKET MESSAGE:', JSON.stringify(data, null, 2))
      const incomingData = data.blockchain_data || data.data
      console.log('🔍 VISITOR DEBUG - Incoming base_fee_gwei:', incomingData?.base_fee_gwei)
      console.log('🔍 VISITOR DEBUG - Full incoming data:', incomingData)

      if (data.blockchain_data) {
        Object.assign(systemState.blockchainData, data.blockchain_data)
      } else if (data.data) {
        Object.assign(systemState.blockchainData, data.data)
      }

      // Debug: Log state after assignment
      console.log('🔍 VISITOR DEBUG - State after assign:', systemState.blockchainData.base_fee_gwei)

      // Check if motor commands are included in blockchain update
      if (data.motor_commands) {
        console.log('Visitor - Motor commands from blockchain:', data.motor_commands)

        // Apply motor commands to update motor states
        Object.keys(data.motor_commands).forEach(motorName => {
          const motorCommand = data.motor_commands[motorName]
          if (systemState.motorStates[motorName] && motorCommand) {
            console.log(`Visitor - Updating motor ${motorName} from blockchain command:`, motorCommand)

            // Update motor state with new command
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
      console.log('Visitor - Motor update received:', data)
      if (data.motor_name && data.state) {
        const oldState = systemState.motorStates[data.motor_name] ? { ...systemState.motorStates[data.motor_name] } : null
        if (systemState.motorStates[data.motor_name]) {
          Object.assign(systemState.motorStates[data.motor_name], data.state)
        } else {
          // Create new motor state if it doesn't exist
          systemState.motorStates[data.motor_name] = data.state
        }
        console.log('Visitor - Motor state updated:', {
          motor: data.motor_name,
          oldState,
          newState: systemState.motorStates[data.motor_name]
        })
      }
      break
  }
}

// Computed values
const isConnected = computed(() => {
  const connected = connectionStatus.value === 'connected'
  console.log('isConnected computed:', connected, 'status:', connectionStatus.value)
  return connected
})
const currentModeDisplay = computed(() => {
  return systemState.mode === 'auto' ? 'Blockchain Auto' : 'Manual Control'
})

// Lifecycle
onMounted(() => {
  connectToServer()
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
      <div class="gap-6">

        <!-- Motor Visualization - Always on top -->
        <div class="w-full space-y-6">
          <MotorVisualization :motor-states="systemState.motorStates" :blockchain-data="systemState.blockchainData"
            :is-active="isConnected" />
        </div>

        <!-- Data Display - Always below -->
        <div class="w-full space-y-6">
          <DataDisplayPanel :system-state="systemState" :is-read-only="true" />
        </div>
      </div>

      <!-- Footer Info -->
      <div class="mt-8 text-center text-gray-400 text-sm">
        <p>Real-time blockchain data drives artistic motor movements • Read-only display</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* Minimal custom styles - most styling handled by Tailwind classes */
</style>