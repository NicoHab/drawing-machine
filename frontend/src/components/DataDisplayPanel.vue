<script setup lang="ts">
import { computed } from 'vue'

// Props
interface Props {
  systemState: {
    mode: string
    blockchainData: {
      eth_price_usd: number
      gas_price_gwei: number
      base_fee_gwei?: number
      blob_space_utilization_percent: number
      block_fullness_percent: number
      block_number: number | string
      epoch: number | string
    }
    motorStates: Record<string, any>
  }
  isReadOnly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isReadOnly: false
})

// Computed
const isAutoMode = computed(() => props.systemState.mode === 'auto')
const isManualMode = computed(() => props.systemState.mode === 'manual')
</script>

<template>
  <div class="data-display-panel">
    <!-- Blockchain Auto Mode Display -->
    <div v-if="isAutoMode" class="bg-gray-800/30 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
      <h2 class="text-2xl font-bold mb-4 text-white">
        {{ isReadOnly ? '📊 Live Blockchain Data' : 'Blockchain Auto Mode' }}
      </h2>
      
      <!-- Block & Epoch Info at Top -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div class="bg-gray-900/50 rounded-lg p-4">
          <h3 class="text-sm font-semibold text-white mb-1">Current Epoch</h3>
          <p class="text-2xl font-bold text-white">
            {{ systemState.blockchainData.epoch || 'N/A' }}
          </p>
        </div>
        
        <div class="bg-gray-900/50 rounded-lg p-4">
          <h3 class="text-sm font-semibold text-white mb-1">Current Block</h3>
          <p class="text-2xl font-bold text-white">
            {{ systemState.blockchainData.block_number || 'Loading...' }}
          </p>
        </div>
      </div>

      <!-- Main Blockchain Data -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-gray-900/50 rounded-lg p-4">
          <h3 class="text-sm font-semibold text-blue-400 mb-1">Canvas - ETH Price</h3>
          <p class="text-2xl font-bold text-white">
            ${{ systemState.blockchainData.eth_price_usd?.toFixed(4) || '0.0000' }}
          </p>
        </div>
        
        <div class="bg-gray-900/50 rounded-lg p-4">
          <h3 class="text-sm font-semibold text-purple-400 mb-1">PB - Blob Utilization</h3>
          <p class="text-2xl font-bold text-white">
            {{ systemState.blockchainData.blob_space_utilization_percent?.toFixed(2) || '0.00' }}<span class="text-sm text-gray-400">%</span>
          </p>
        </div>
        
        <div class="bg-gray-900/50 rounded-lg p-4">
          <h3 class="text-sm font-semibold text-green-400 mb-1">PCD - Gas Target Ratio</h3>
          <p class="text-2xl font-bold text-white">
            <template v-if="systemState.blockchainData.base_fee_gwei && systemState.blockchainData.base_fee_gwei > 0">
              {{ ((systemState.blockchainData.gas_price_gwei / systemState.blockchainData.base_fee_gwei) * 100).toFixed(1) }}<span class="text-sm text-gray-400">%</span>
            </template>
            <template v-else>
              <span class="text-lg text-orange-400">{{ systemState.blockchainData.gas_price_gwei?.toFixed(1) || '0.0' }}</span> <span class="text-sm text-gray-400">gwei*</span>
            </template>
          </p>
          <template v-if="!(systemState.blockchainData.base_fee_gwei && systemState.blockchainData.base_fee_gwei > 0)">
            <p class="text-xs text-gray-500 mt-1">*Base fee data pending</p>
          </template>
        </div>
        
        <div class="bg-gray-900/50 rounded-lg p-4">
          <h3 class="text-sm font-semibold text-orange-400 mb-1">PE - Block Utilization</h3>
          <p class="text-2xl font-bold text-white">
            {{ systemState.blockchainData.block_fullness_percent?.toFixed(2) || '0.00' }}<span class="text-sm text-gray-400">%</span>
          </p>
        </div>
      </div>
      
      <div class="mt-4 text-sm text-gray-400">
        {{ isReadOnly ? 'Motors respond automatically to live Ethereum blockchain data' : 'Motors are automatically controlled by live Ethereum blockchain data' }}
      </div>
    </div>

    <!-- Manual Mode Display -->
    <div v-else-if="isManualMode" class="bg-gray-800/30 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
      <h2 class="text-2xl font-bold mb-4 text-white">
        {{ isReadOnly ? '🎮 Manual Control Status' : 'Manual Control Mode' }}
      </h2>
      
      <!-- Motor Status Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="(state, motorName) in systemState.motorStates" :key="motorName" class="bg-gray-900/50 rounded-lg p-4">
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-sm font-semibold text-white mb-1">
                {{ motorName.replace('motor_', '').toUpperCase() }}
              </h3>
              <p class="text-lg font-bold text-white">
                {{ (state.velocity_rpm || 0).toFixed(1) }} RPM
              </p>
            </div>
            <div class="text-right">
              <div class="text-sm text-gray-400">Direction</div>
              <div class="text-sm font-semibold text-blue-400">{{ state.direction || 'CW' }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="mt-4 text-sm text-gray-400">
        {{ isReadOnly ? 'Motors are currently under manual control by the operator' : 'Manually control individual motor speeds and directions' }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.data-display-panel {
  /* Consistent styling handled by Tailwind classes */
}

/* Responsive adjustments - ensure single column on small screens only */
@media (max-width: 767px) {
  .grid-cols-4,
  .grid-cols-2 {
    grid-template-columns: 1fr !important;
  }
}
</style>