<script setup lang="ts">
import { computed } from 'vue'

// Props
interface Props {
  currentMode: string
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  modeChange: [mode: string]
}>()

// Available modes
const modes = [
  {
    value: 'manual',
    label: 'Manual Control',
    description: 'Direct user control of motors',
    icon: '🎮'
  },
  {
    value: 'auto',
    label: 'Blockchain Auto',
    description: 'Automatic control from live Ethereum data',
    icon: '⛓️'
  },
  {
    value: 'hybrid',
    label: 'Hybrid Mode',
    description: 'Mix of automatic and manual control',
    icon: '🔀'
  },
  {
    value: 'offline',
    label: 'Offline Drawing',
    description: 'Execute pre-computed drawing sequences',
    icon: '📁'
  }
]

// Computed
const currentModeInfo = computed(() => {
  return modes.find(mode => mode.value === props.currentMode) || modes[0]
})

// Track if we're currently processing a mode change
let isChangingMode = false

// Methods  
const selectMode = (modeValue: string, event?: MouseEvent) => {
  // Prevent any action if we're already changing mode
  if (isChangingMode) {
    return
  }
  
  // Prevent double-clicks and rapid clicks
  if (event) {
    event.preventDefault()
    event.stopPropagation()
    
    if (!event.isTrusted) {
      return
    }
  }
  
  // Only proceed if actually changing to a different mode
  if (modeValue === props.currentMode) {
    return
  }
  
  // Set flag to prevent concurrent changes
  isChangingMode = true
  
  // Emit the change
  emit('modeChange', modeValue)
  
  // Clear flag after a delay to prevent rapid changes
  setTimeout(() => {
    isChangingMode = false
  }, 1000)
}
</script>

<template>
  <div class="mode-selector">
    <h2>Control Mode</h2>
    
    <div class="current-mode">
      <div class="mode-indicator">
        <span class="mode-icon">{{ currentModeInfo.icon }}</span>
        <div class="mode-info">
          <h3>{{ currentModeInfo.label }}</h3>
          <p>{{ currentModeInfo.description }}</p>
        </div>
      </div>
    </div>

    <div class="mode-options">
      <button
        v-for="mode in modes"
        :key="mode.value"
        class="mode-option"
        :class="{ active: mode.value === currentMode }"
        @click="selectMode(mode.value, $event)"
      >
        <span class="mode-icon">{{ mode.icon }}</span>
        <div class="mode-details">
          <span class="mode-label">{{ mode.label }}</span>
          <span class="mode-description">{{ mode.description }}</span>
        </div>
      </button>
    </div>

    <div class="mode-help">
      <h4>Mode Descriptions:</h4>
      <ul>
        <li><strong>Manual:</strong> Full user control via sliders, presets, and manual commands</li>
        <li><strong>Blockchain Auto:</strong> Motors respond automatically to live Ethereum price and network data</li>
        <li><strong>Hybrid:</strong> Automatic baseline with manual override capabilities</li>
        <li><strong>Offline:</strong> Execute pre-designed drawing patterns without internet</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.mode-selector {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
}

.mode-selector h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #2c3e50;
}

.current-mode {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #3498db;
}

.mode-indicator {
  display: flex;
  align-items: center;
  gap: 15px;
}

.mode-icon {
  font-size: 24px;
}

.mode-info h3 {
  margin: 0 0 5px 0;
  color: #2c3e50;
}

.mode-info p {
  margin: 0;
  color: #6c757d;
  font-size: 14px;
}

.mode-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}

.mode-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
  text-align: left;
}

.mode-option:hover {
  border-color: #3498db;
  background: #f8f9fa;
}

.mode-option.active {
  border-color: #3498db;
  background: #e3f2fd;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.mode-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mode-label {
  font-weight: 500;
  color: #2c3e50;
}

.mode-description {
  font-size: 12px;
  color: #6c757d;
}

.mode-help {
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #17a2b8;
}

.mode-help h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #2c3e50;
}

.mode-help ul {
  margin: 0;
  padding-left: 20px;
}

.mode-help li {
  margin-bottom: 8px;
  color: #495057;
  font-size: 14px;
}

.mode-help li:last-child {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .mode-options {
    grid-template-columns: 1fr;
  }
  
  .mode-option {
    padding: 15px;
  }
}
</style>