<script setup lang="ts">
import { ref, onMounted } from 'vue'
import MotorControl from '../components/MotorControl.vue'
import MotorVisualization from '../components/MotorVisualization.vue'
import ModeSelector from '../components/ModeSelector.vue'
import DataDisplayPanel from '../components/DataDisplayPanel.vue'
import { MOTOR_CONFIG } from '../config/constants'
import { useWebSocket } from '../composables/useWebSocket'

// WebSocket connection using composable
const wsUrl = import.meta.env.VITE_BACKEND_URL || 'wss://drawing-machine-production.up.railway.app'
const apiKey = ref('')

const { 
  connectionStatus, 
  systemState, 
  connect, 
  sendMotorCommand, 
  switchMode, 
  emergencyStop, 
  updateApiKey 
} = useWebSocket({
  url: wsUrl,
  clientType: 'web_ui',
  apiKey: apiKey.value,
  autoReconnect: true
})

// API key change handler
const onApiKeyChange = () => {
  updateApiKey(apiKey.value)
}

onMounted(() => {
  connect()
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
              :motor-name="motorName as string" :motor-state="state" :safety-limit="MOTOR_CONFIG.SAFETY_LIMIT_RPM"
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