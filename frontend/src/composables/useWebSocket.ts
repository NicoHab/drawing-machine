/**
 * WebSocket Composable
 * Reusable WebSocket connection management with message handling
 */

import { ref, reactive, onUnmounted } from 'vue'
import { WEBSOCKET_CONFIG } from '../config/constants'

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected'

export interface WebSocketMessage {
  type: string
  [key: string]: any
}

export interface WebSocketOptions {
  url: string
  clientType: 'web_ui' | 'visitor'
  apiKey?: string
  autoReconnect?: boolean
  reconnectDelay?: number
}

export interface SystemState {
  mode: string
  motorStates: Record<string, any>
  blockchainData: {
    eth_price_usd: number
    gas_price_gwei: number
    base_fee_gwei?: number
    blob_space_utilization_percent: number
    block_fullness_percent: number
    block_number: number | string
    epoch: number | string
  }
}

export function useWebSocket(options: WebSocketOptions) {
  // Connection state
  const ws = ref<WebSocket | null>(null)
  const connectionStatus = ref<ConnectionStatus>('disconnected')

  // System state
  const systemState = reactive<SystemState>({
    mode: options.clientType === 'visitor' ? 'auto' : 'manual',
    motorStates: {
      motor_canvas: { velocity_rpm: 0, direction: 'CW', last_update: Date.now() / 1000, is_enabled: true },
      motor_pb: { velocity_rpm: 0, direction: 'CW', last_update: Date.now() / 1000, is_enabled: true },
      motor_pcd: { velocity_rpm: 0, direction: 'CW', last_update: Date.now() / 1000, is_enabled: true },
      motor_pe: { velocity_rpm: 0, direction: 'CW', last_update: Date.now() / 1000, is_enabled: true }
    },
    blockchainData: {
      eth_price_usd: 0,
      gas_price_gwei: 0,
      base_fee_gwei: 0,
      blob_space_utilization_percent: 0,
      block_fullness_percent: 0,
      block_number: options.clientType === 'visitor' ? 0 : 'Loading...',
      epoch: options.clientType === 'visitor' ? 0 : 'N/A'
    }
  })

  // Message handling state
  let lastModeChangeTime = 0

  // Connect to WebSocket
  const connect = () => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      return
    }

    connectionStatus.value = 'connecting'
    ws.value = new WebSocket(options.url)

    ws.value.onopen = () => {
      // Stay in 'connecting' state until authenticated
      // Send authentication
      const authMessage = {
        type: 'authenticate',
        client_type: options.clientType,
        user_info: {},
        api_key: options.apiKey || ''
      }
      ws.value?.send(JSON.stringify(authMessage))
    }

    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleMessage(data)
      } catch (error) {
        console.error(`Failed to parse WebSocket message:`, error)
      }
    }

    ws.value.onclose = () => {
      connectionStatus.value = 'disconnected'
      
      // Auto-reconnect if enabled
      if (options.autoReconnect !== false) {
        const delay = options.reconnectDelay || 
          (options.clientType === 'visitor' ? 
            WEBSOCKET_CONFIG.VISITOR_RECONNECT_DELAY : 
            WEBSOCKET_CONFIG.RECONNECT_DELAY)
        setTimeout(connect, delay)
      }
    }

    ws.value.onerror = (error) => {
      console.error(`WebSocket error:`, error)
      connectionStatus.value = 'disconnected'
    }
  }

  // Handle incoming messages
  const handleMessage = (data: WebSocketMessage) => {
    switch (data.type) {
      case 'authenticated':
        connectionStatus.value = 'connected'
        if (data.api_access === false) {
          if (options.clientType === 'web_ui') {
            alert('Demo mode: Blockchain API disabled. Enter API key to enable live data.')
          }
        }
        break

      case 'system_state':
        const now = Date.now()
        if (now - lastModeChangeTime > WEBSOCKET_CONFIG.MODE_CHANGE_DEBOUNCE) {
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
        
        // Prepare motor state updates first to ensure atomic update
        const motorUpdates: Record<string, any> = {}
        if (data.motor_commands) {
          Object.keys(data.motor_commands).forEach(motorName => {
            const motorCommand = data.motor_commands[motorName]
            if (systemState.motorStates[motorName] && motorCommand) {
              motorUpdates[motorName] = {
                velocity_rpm: motorCommand.velocity_rpm || 0,
                direction: motorCommand.direction || 'CW',
                last_update: Date.now() / 1000,
                is_enabled: true
              }
            }
          })
        }

        // Atomic update: Apply blockchain data and motor states simultaneously
        if (data.blockchain_data) {
          Object.assign(systemState.blockchainData, data.blockchain_data)
        } else if (data.data) {
          Object.assign(systemState.blockchainData, data.data)
        }
        
        // Apply motor updates immediately after blockchain data
        Object.keys(motorUpdates).forEach(motorName => {
          Object.assign(systemState.motorStates[motorName], motorUpdates[motorName])
        })
        break

      case 'motor_state_update':
      case 'motor_update':
        if (data.motor_name && data.state) {
          if (systemState.motorStates[data.motor_name]) {
            Object.assign(systemState.motorStates[data.motor_name], data.state)
          } else {
            systemState.motorStates[data.motor_name] = data.state
          }
        }
        break

      case 'motor_command_executed':
        // Motor command executed - no action needed for state
        break

      case 'authentication_failed':
        console.error(`Authentication failed:`, data)
        console.error(`Sent client_type: ${options.clientType}, api_key: "${options.apiKey || ''}"`)
        connectionStatus.value = 'disconnected'
        break
    }
  }

  // Send message
  const sendMessage = (message: WebSocketMessage) => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(message))
    } else {
      console.error('WebSocket not connected, status:', connectionStatus.value)
    }
  }

  // Send motor command (admin only)
  const sendMotorCommand = (motorName: string, velocity: number, direction: string) => {
    sendMessage({
      type: 'motor_command',
      motor_name: motorName,
      velocity_rpm: velocity,
      direction: direction
    })
  }

  // Switch mode (admin only)
  const switchMode = (newMode: string) => {
    lastModeChangeTime = Date.now()
    sendMessage({
      type: 'mode_change',
      mode: newMode
    })
  }

  // Emergency stop (admin only)
  const emergencyStop = () => {
    sendMessage({
      type: 'emergency_stop'
    })
  }

  // Update API key and re-authenticate
  const updateApiKey = (newApiKey: string) => {
    options.apiKey = newApiKey
    sendMessage({
      type: 'authenticate',
      client_type: options.clientType,
      user_info: {},
      api_key: newApiKey
    })
  }

  // Disconnect
  const disconnect = () => {
    if (ws.value) {
      ws.value.close()
    }
  }

  // Cleanup on unmount
  onUnmounted(() => {
    disconnect()
  })

  return {
    // State
    ws,
    connectionStatus,
    systemState,

    // Methods
    connect,
    disconnect,
    sendMessage,
    sendMotorCommand,
    switchMode,
    emergencyStop,
    updateApiKey
  }
}