<template>
  <div id="app">
    <router-view class="app-view"></router-view>
  </div>
</template>

<script>
export default {
  name: 'app',
}
</script>

<style>
#app {
  min-height: 100vh;
  background: transparent;
}

.app-view {
  min-height: 100vh;
}
</style>

