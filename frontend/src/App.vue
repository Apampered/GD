<!-- frontend/src/App.vue -->
<script setup>
import HomeView from './views/HomeView.vue'
</script>

<template>
  <div class="app-container">
    <el-container>
      <el-header height="60px">
        <h1>智能生成平台</h1>
        <p style="margin: 0; color: #666;">基于 ComfyScript 的低门槛 AI 绘画工具</p>
      </el-header>

      <el-main>
        <HomeView />
      </el-main>
    </el-container>
  </div>
</template>

<style>
.app-container {
  height: 100vh;
  background: #f5f7fa;
}
.el-header {
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
h1 {
  margin: 0;
  font-size: 24px;
  color: #409eff;
}
</style>