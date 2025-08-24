/**
 * Application Constants
 * Centralized configuration for magic numbers and hard-coded values
 */

// WebSocket Configuration
export const WEBSOCKET_CONFIG = {
  RECONNECT_DELAY: 3000, // Auto-reconnect delay in milliseconds
  VISITOR_RECONNECT_DELAY: 5000, // Visitor reconnect delay in milliseconds
  MODE_CHANGE_DEBOUNCE: 2000 // Debounce time for mode changes
} as const

// Motor Configuration
export const MOTOR_CONFIG = {
  SAFETY_LIMIT_RPM: 50, // Default safety limit for motor RPM
  CANVAS_WIDTH: 600, // Motor visualization canvas width
  CANVAS_HEIGHT: 400, // Motor visualization canvas height
  MOTOR_RADIUS: 40, // Motor visualization radius
  ANIMATION_SCALE: 0.1 // Motor rotation animation scale factor
} as const

// UI Configuration  
export const UI_CONFIG = {
  DECIMAL_PLACES: {
    ETH_PRICE: 4, // ETH price decimal places
    PERCENTAGE: 2, // Percentage value decimal places
    PERCENTAGE_PRECISE: 1, // Precise percentage decimal places
    GAS_PRICE: 1 // Gas price decimal places
  }
} as const

// Default Values
export const DEFAULT_VALUES = {
  MOTOR_DIRECTION: 'CW',
  MOTOR_RPM: 0,
  BLOCKCHAIN_FALLBACK: {
    ETH_PRICE: '0.0000',
    PERCENTAGE: '0.00',
    PERCENTAGE_PRECISE: '0.0',
    GAS_PRICE: '0.0'
  }
} as const

// Activity Thresholds for motor visualization colors
export const ACTIVITY_THRESHOLDS = {
  HIGH_ACTIVITY_RPM: 15, // Red color threshold
  MEDIUM_ACTIVITY_RPM: 10, // Orange color threshold  
  LOW_ACTIVITY_RPM: 0 // Green color threshold
} as const