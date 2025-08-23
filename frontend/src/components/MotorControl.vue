<script setup lang="ts">
import { ref, computed, watch } from 'vue'

// Props
interface Props {
  motorName: string
  motorState: {
    velocity_rpm: number
    direction: string
    last_update: number
    is_enabled: boolean
  }
  safetyLimit: number
  disabled: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  motorCommand: [motorName: string, velocityRpm: number, direction: string]
}>()

// Local state
const velocity = ref(0)
const direction = ref('CW')

// Watch motor state changes and update local controls
watch(() => props.motorState, (newState) => {
  if (newState) {
    velocity.value = newState.velocity_rpm
    direction.value = newState.direction
  }
}, { immediate: true })

// Computed properties
const motorDisplayName = computed(() => {
  const nameMap: Record<string, string> = {
    'motor_canvas': 'Canvas',
    'motor_pb': 'PB',
    'motor_pcd': 'PCD', 
    'motor_pe': 'PE'
  }
  return nameMap[props.motorName] || props.motorName
})

const isActive = computed(() => {
  return Math.abs(props.motorState?.velocity_rpm || 0) > 0.1
})

const lastUpdateText = computed(() => {
  if (!props.motorState?.last_update) return 'Never'
  const seconds = Math.floor((Date.now() / 1000) - props.motorState.last_update)
  return seconds < 60 ? `${seconds}s ago` : `${Math.floor(seconds / 60)}m ago`
})

// Methods
const sendCommand = (rpm: number) => {
  // Negative RPM = CCW, Positive RPM = CW
  const actualVelocity = Math.abs(rpm)
  const actualDirection = rpm >= 0 ? 'CW' : 'CCW'
  
  velocity.value = actualVelocity
  direction.value = actualDirection
  
  emit('motorCommand', props.motorName, actualVelocity, actualDirection)
}

const stopMotor = () => {
  sendCommand(0)
}

// Preset velocity buttons - negative values mean CCW
const setPresetVelocity = (preset: number) => {
  sendCommand(preset)
}
</script>

<template>
  <div class="motor-control" :class="{ active: isActive, disabled: disabled || !motorState?.is_enabled }">
    <header class="motor-header">
      <h3>{{ motorDisplayName }}</h3>
      <div class="motor-status">
        <span class="status-indicator" :class="{ 
          active: isActive,
          disabled: !motorState?.is_enabled 
        }"></span>
        <span class="last-update">{{ lastUpdateText }}</span>
      </div>
    </header>

    <div class="motor-controls">
      <!-- Current State Display -->
      <div class="current-state">
        <div class="state-value">
          <span class="rpm-value">{{ 
            motorState?.direction === 'CCW' 
              ? '-' + (motorState?.velocity_rpm?.toFixed(1) || '0')
              : (motorState?.velocity_rpm?.toFixed(1) || '0')
          }}</span>
          <span class="rpm-unit">RPM</span>
        </div>
      </div>

      <!-- Preset Buttons -->
      <div class="preset-controls">
        <div class="preset-grid">
          <!-- Negative presets (CCW) -->
          <button
            v-for="preset in [-20, -18, -16, -14, -12, -10, -8, -6, -4, -2]"
            :key="preset"
            :disabled="disabled || !motorState?.is_enabled"
            @click="setPresetVelocity(preset)"
            class="preset-btn negative"
            :class="{ 
              active: motorState?.direction === 'CCW' && Math.abs(motorState?.velocity_rpm - Math.abs(preset)) < 0.1
            }"
          >
            {{ preset }}
          </button>
          
          <!-- Stop button -->
          <button
            :disabled="disabled"
            @click="stopMotor"
            class="preset-btn stop"
            :class="{ active: Math.abs(motorState?.velocity_rpm || 0) < 0.1 }"
          >
            0
          </button>
          
          <!-- Positive presets (CW) -->
          <button
            v-for="preset in [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]"
            :key="preset"
            :disabled="disabled || !motorState?.is_enabled"
            @click="setPresetVelocity(preset)"
            class="preset-btn positive"
            :class="{ 
              active: motorState?.direction === 'CW' && Math.abs(motorState?.velocity_rpm - preset) < 0.1
            }"
          >
            +{{ preset }}
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.motor-control {
  border: 2px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  background: white;
  transition: all 0.3s;
}

.motor-control.active {
  border-color: #27ae60;
  box-shadow: 0 0 10px rgba(39, 174, 96, 0.3);
}

.motor-control.disabled {
  opacity: 0.6;
  background: #f8f9fa;
}

.motor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.motor-header h3 {
  margin: 0;
  color: #2c3e50;
}

.motor-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #bdc3c7;
  transition: background-color 0.3s;
}

.status-indicator.active {
  background: #27ae60;
}

.status-indicator.disabled {
  background: #e74c3c;
}

.last-update {
  font-size: 12px;
  color: #7f8c8d;
}

.motor-controls {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.current-state {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 6px;
  text-align: center;
  margin-bottom: 15px;
}

.state-value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8px;
}

.rpm-value {
  font-size: 32px;
  font-weight: bold;
  color: #2c3e50;
  font-family: 'Courier New', monospace;
}

.rpm-unit {
  font-size: 14px;
  color: #6c757d;
  font-weight: 500;
}

.preset-controls {
  margin-top: 10px;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(50px, 1fr));
  gap: 6px;
}

.preset-btn {
  padding: 10px 6px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 13px;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.preset-btn:hover:not(:disabled) {
  background: #f8f9fa;
  transform: translateY(-1px);
}

.preset-btn.negative {
  color: #e74c3c;
  border-color: #ffcccc;
}

.preset-btn.negative:hover:not(:disabled) {
  background: #fff5f5;
}

.preset-btn.positive {
  color: #27ae60;
  border-color: #ccffcc;
}

.preset-btn.positive:hover:not(:disabled) {
  background: #f5fff5;
}

.preset-btn.stop {
  color: #6c757d;
  font-weight: bold;
  border-color: #adb5bd;
}

.preset-btn.stop:hover:not(:disabled) {
  background: #f8f9fa;
}

.preset-btn.active {
  font-weight: bold;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.3);
}

.preset-btn.negative.active {
  background: #e74c3c;
  color: white;
  border-color: #e74c3c;
}

.preset-btn.positive.active {
  background: #27ae60;
  color: white;
  border-color: #27ae60;
}

.preset-btn.stop.active {
  background: #6c757d;
  color: white;
  border-color: #6c757d;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>