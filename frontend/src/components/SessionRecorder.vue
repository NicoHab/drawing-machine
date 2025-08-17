<script setup lang="ts">
import { ref, reactive } from 'vue'

// Props
interface Props {
  recordingActive: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  startRecording: [sessionName: string]
  stopRecording: []
  sendMessage: [message: any]
}>()

// Local state
const sessionName = ref('')
const recordings = reactive<any[]>([])
const showRecordings = ref(false)

// Methods
const startRecording = () => {
  if (!sessionName.value.trim()) {
    sessionName.value = `Session ${new Date().toLocaleString()}`
  }
  emit('startRecording', sessionName.value)
  sessionName.value = ''
}

const stopRecording = () => {
  emit('stopRecording')
}

const loadRecordings = () => {
  emit('sendMessage', { type: 'get_recordings' })
  showRecordings.value = true
}

const playbackSession = (sessionId: string) => {
  if (confirm(`Start playback of session: ${sessionId}?`)) {
    emit('sendMessage', {
      type: 'playback_session',
      session_id: sessionId
    })
  }
}

const formatDuration = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const formatDate = (timestamp: number): string => {
  return new Date(timestamp * 1000).toLocaleString()
}

// Handle incoming recordings list
const handleRecordingsList = (recordingsList: any[]) => {
  recordings.splice(0, recordings.length, ...recordingsList)
}

// Expose method for parent component
defineExpose({
  handleRecordingsList
})
</script>

<template>
  <div class="session-recorder">
    <h2>Session Recording</h2>

    <!-- Recording Controls -->
    <div class="recording-controls">
      <div class="record-section">
        <h3>
          <span class="record-indicator" :class="{ active: recordingActive }">●</span>
          {{ recordingActive ? 'Recording Active' : 'Record New Session' }}
        </h3>
        
        <div v-if="!recordingActive" class="start-recording">
          <input
            v-model="sessionName"
            type="text"
            placeholder="Session name (optional)"
            @keyup.enter="startRecording"
            class="session-name-input"
          />
          <button @click="startRecording" class="start-btn">
            ⏺ Start Recording
          </button>
        </div>

        <div v-else class="recording-active">
          <p class="recording-status">
            Recording session commands and timing...
          </p>
          <button @click="stopRecording" class="stop-btn">
            ⏹ Stop Recording
          </button>
        </div>
      </div>
    </div>

    <!-- Playback Controls -->
    <div class="playback-controls">
      <h3>Session Playback</h3>
      
      <div class="playback-section">
        <button @click="loadRecordings" class="load-btn">
          📁 Load Saved Sessions
        </button>
        
        <div v-if="showRecordings" class="recordings-list">
          <h4>Saved Sessions ({{ recordings.length }})</h4>
          
          <div v-if="recordings.length === 0" class="no-recordings">
            No recorded sessions found.
          </div>
          
          <div v-else class="recordings-grid">
            <div
              v-for="recording in recordings"
              :key="recording.session_id"
              class="recording-item"
            >
              <div class="recording-header">
                <h5>{{ recording.name }}</h5>
                <span class="recording-mode">{{ recording.mode.toUpperCase() }}</span>
              </div>
              
              <div class="recording-details">
                <div class="detail-item">
                  <label>Duration:</label>
                  <span>{{ formatDuration(recording.duration) }}</span>
                </div>
                <div class="detail-item">
                  <label>Commands:</label>
                  <span>{{ recording.command_count }}</span>
                </div>
                <div class="detail-item">
                  <label>Recorded:</label>
                  <span>{{ formatDate(recording.start_time) }}</span>
                </div>
              </div>
              
              <div class="recording-actions">
                <button
                  @click="playbackSession(recording.session_id)"
                  class="playback-btn"
                >
                  ▶ Playback
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Help Section -->
    <div class="help-section">
      <h4>How to Use:</h4>
      <ul>
        <li><strong>Recording:</strong> Start recording to capture all motor commands and their timing</li>
        <li><strong>Playback:</strong> Replay recorded sessions with original timing and commands</li>
        <li><strong>Sessions:</strong> Each session includes command sequence, timing, and safety settings</li>
        <li><strong>Notes:</strong> Recording works in any control mode, playback switches to manual mode</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.session-recorder {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
}

.session-recorder h2 {
  margin-top: 0;
  color: #2c3e50;
}

.recording-controls,
.playback-controls {
  margin-bottom: 25px;
}

.record-section h3,
.playback-section h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
  color: #495057;
}

.record-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #6c757d;
  transition: all 0.3s;
}

.record-indicator.active {
  background: #dc3545;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.1); }
}

.start-recording {
  display: flex;
  gap: 10px;
  align-items: center;
}

.session-name-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.start-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  background: #dc3545;
  color: white;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s;
}

.start-btn:hover {
  background: #c82333;
}

.recording-active {
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #dc3545;
}

.recording-status {
  margin: 0 0 10px 0;
  color: #495057;
}

.stop-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  background: #6c757d;
  color: white;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s;
}

.stop-btn:hover {
  background: #545b62;
}

.load-btn {
  padding: 10px 20px;
  border: 1px solid #007bff;
  border-radius: 4px;
  background: white;
  color: #007bff;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
}

.load-btn:hover {
  background: #007bff;
  color: white;
}

.recordings-list {
  margin-top: 20px;
}

.recordings-list h4 {
  color: #495057;
  margin-bottom: 15px;
}

.no-recordings {
  text-align: center;
  padding: 30px;
  color: #6c757d;
  font-style: italic;
}

.recordings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.recording-item {
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 15px;
  background: white;
  transition: all 0.3s;
}

.recording-item:hover {
  border-color: #007bff;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.1);
}

.recording-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.recording-header h5 {
  margin: 0;
  color: #2c3e50;
}

.recording-mode {
  font-size: 11px;
  padding: 2px 6px;
  background: #e9ecef;
  border-radius: 3px;
  color: #495057;
  font-weight: 500;
}

.recording-details {
  margin-bottom: 15px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 14px;
}

.detail-item label {
  color: #6c757d;
  font-weight: 500;
}

.detail-item span {
  color: #495057;
}

.recording-actions {
  text-align: center;
}

.playback-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: #28a745;
  color: white;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s;
}

.playback-btn:hover {
  background: #218838;
}

.help-section {
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #ffc107;
}

.help-section h4 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #2c3e50;
}

.help-section ul {
  margin: 0;
  padding-left: 20px;
}

.help-section li {
  margin-bottom: 8px;
  color: #495057;
  font-size: 14px;
}

.help-section li:last-child {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .start-recording {
    flex-direction: column;
    align-items: stretch;
  }
  
  .recordings-grid {
    grid-template-columns: 1fr;
  }
}
</style>