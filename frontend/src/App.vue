<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div id="app">
    <RouterView />
  </div>
</template>

<style>
#app {
  min-height: 100vh;
}

/* Global styles for consistency */
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
}
</style>