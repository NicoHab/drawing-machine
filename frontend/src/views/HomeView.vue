<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Redirect to visitor view immediately
onMounted(() => {
  router.push('/visitor')
})
</script>

<template>
  <div class="home-redirect">
    <div class="loading-message">
      <h2>🎨 Blockchain Drawing Machine</h2>
      <p>Redirecting to display...</p>
    </div>
  </div>
</template>

<style scoped>
.home-redirect {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
  color: white;
}

.loading-message {
  text-align: center;
}

.loading-message h2 {
  margin-bottom: 1rem;
  font-size: 2rem;
}

.loading-message p {
  color: rgba(255, 255, 255, 0.7);
}
</style>