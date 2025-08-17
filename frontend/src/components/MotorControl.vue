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
    'motor_canvas': 'Canvas Motor',
    'motor_pb': 'Pen Brush',
    'motor_pcd': 'Pen Color Depth', 
    'motor_pe': 'Pen Elevation'
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
const sendCommand = () => {
  emit('motorCommand', props.motorName, velocity.value, direction.value)
}

const stopMotor = () => {
  velocity.value = 0
  emit('motorCommand', props.motorName, 0, direction.value)
}

const onVelocityChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  velocity.value = parseFloat(target.value)
  sendCommand()
}

const onDirectionChange = () => {
  sendCommand()
}

// Preset velocity buttons
const setPresetVelocity = (preset: number) => {
  velocity.value = preset
  sendCommand()
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
        <div class="state-item">
          <label>Current RPM:</label>
          <span class="rpm-value">{{ motorState?.velocity_rpm?.toFixed(1) || 0 }}</span>
        </div>
        <div class="state-item">
          <label>Direction:</label>
          <span class="direction-value">{{ motorState?.direction || 'CW' }}</span>
        </div>
      </div>

      <!-- Velocity Control -->
      <div class="velocity-control">
        <label>Target Velocity (RPM)</label>
        <div class="velocity-input-group">
          <input
            type="range"
            :min="-safetyLimit"
            :max="safetyLimit"
            :step="0.1"
            v-model.number="velocity"
            :disabled="disabled || !motorState?.is_enabled"
            @input="onVelocityChange"
            class="velocity-slider"
          />
          <input
            type="number"
            :min="-safetyLimit"
            :max="safetyLimit"
            :step="0.1"
            v-model.number="velocity"
            :disabled="disabled || !motorState?.is_enabled"
            @change="sendCommand"
            class="velocity-input"
          />
        </div>
        <div class="velocity-range">
          <span>-{{ safetyLimit }}</span>
          <span>{{ safetyLimit }}</span>
        </div>
      </div>

      <!-- Direction Control -->
      <div class="direction-control">
        <label>Direction</label>
        <div class="direction-buttons">
          <button
            :class="{ active: direction === 'CW' }"
            :disabled="disabled || !motorState?.is_enabled"
            @click="direction = 'CW'; onDirectionChange()"
          >
            ↻ CW
          </button>
          <button
            :class="{ active: direction === 'CCW' }"
            :disabled="disabled || !motorState?.is_enabled"
            @click="direction = 'CCW'; onDirectionChange()"
          >
            ↺ CCW
          </button>
        </div>
      </div>

      <!-- Preset Buttons -->
      <div class="preset-controls">
        <label>Quick Presets</label>
        <div class="preset-buttons">
          <button
            v-for="preset in [0, 10, 25, 50, -10, -25]"
            :key="preset"
            :disabled="disabled || !motorState?.is_enabled"
            @click="setPresetVelocity(preset)"
            class="preset-btn"
            :class="{ 
              active: Math.abs(velocity - preset) < 0.1,
              negative: preset < 0
            }"
          >
            {{ preset }}
          </button>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <button
          class="stop-btn"
          :disabled="disabled"
          @click="stopMotor"
        >
          ⏹ STOP
        </button>
        <button
          class="send-btn"
          :disabled="disabled || !motorState?.is_enabled"
          @click="sendCommand"
        >
          ▶ SEND
        </button>
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
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.state-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.state-item label {
  font-size: 12px;
  color: #6c757d;
  font-weight: 500;
}

.rpm-value {
  font-size: 18px;
  font-weight: bold;
  color: #2c3e50;
}

.direction-value {
  font-size: 16px;
  font-weight: 500;
  color: #495057;
}

.velocity-control label,
.direction-control label,
.preset-controls label {
  font-weight: 500;
  color: #495057;
  display: block;
  margin-bottom: 8px;
}

.velocity-input-group {
  display: flex;
  gap: 10px;
  align-items: center;
}

.velocity-slider {
  flex: 1;
  height: 6px;
  background: #ddd;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}

.velocity-slider::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  background: #3498db;
  border-radius: 50%;
  cursor: pointer;
}

.velocity-input {
  width: 80px;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  text-align: center;
}

.velocity-range {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #6c757d;
  margin-top: 5px;
}

.direction-buttons {
  display: flex;
  gap: 10px;
}

.direction-buttons button {
  flex: 1;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
}

.direction-buttons button:hover:not(:disabled) {
  background: #f8f9fa;
}

.direction-buttons button.active {
  background: #3498db;
  color: white;
  border-color: #3498db;
}

.preset-buttons {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.preset-btn {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
}

.preset-btn:hover:not(:disabled) {
  background: #f8f9fa;
}

.preset-btn.active {
  background: #27ae60;
  color: white;
  border-color: #27ae60;
}

.preset-btn.negative {
  color: #e74c3c;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.stop-btn,
.send-btn {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.stop-btn {
  background: #e74c3c;
  color: white;
}

.stop-btn:hover:not(:disabled) {
  background: #c0392b;
}

.send-btn {
  background: #27ae60;
  color: white;
}

.send-btn:hover:not(:disabled) {
  background: #229954;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>