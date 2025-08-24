<script setup lang="ts">
import { onMounted, computed } from 'vue'
import MotorVisualization from '../components/MotorVisualization.vue'
import DataDisplayPanel from '../components/DataDisplayPanel.vue'
import { useWebSocket } from '../composables/useWebSocket'

// WebSocket connection using composable
const wsUrl = import.meta.env.VITE_BACKEND_URL || 'wss://drawing-machine-production.up.railway.app'

const { 
  connectionStatus, 
  systemState, 
  connect 
} = useWebSocket({
  url: wsUrl,
  clientType: 'visitor',
  autoReconnect: true
})

// Computed values
const isConnected = computed(() => {
  return connectionStatus.value === 'connected'
})

const currentModeDisplay = computed(() => {
  return systemState.mode === 'auto' ? 'Blockchain Auto' : 'Manual Control'
})

// Lifecycle
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