<script setup>
import { onMounted, ref } from 'vue'

const backendStatus = ref('checking')
const backendDetail = ref('正在连接 FastAPI...')

async function checkBackend() {
  backendStatus.value = 'checking'
  backendDetail.value = '正在连接 FastAPI...'

  try {
    const response = await fetch('/api/health')
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const data = await response.json()
    backendStatus.value = 'ok'
    backendDetail.value = `${data.service} · v${data.version} · ${data.timestamp}`
  } catch (error) {
    backendStatus.value = 'error'
    backendDetail.value = `后端未连接：${error.message}`
  }
}

onMounted(checkBackend)
</script>

<template>
  <main class="shell">
    <p class="eyebrow">化工实验室动态风险闭环监护系统</p>
    <h1>危知先觉</h1>
    <p class="subtitle">阶段 1 · 工程环境与基础链路</p>

    <section class="card">
      <div class="status-row">
        <span class="status-dot" :class="backendStatus"></span>
        <strong>FastAPI 后端</strong>
        <span class="status-text">{{ backendStatus }}</span>
      </div>
      <p class="detail">{{ backendDetail }}</p>
      <button type="button" @click="checkBackend">重新检查</button>
    </section>

    <section class="grid">
      <article>
        <span>01</span>
        <h2>视觉检测</h2>
        <p>YOLO11n 已完成六类目标检测的数据与模型准备入口。</p>
      </article>
      <article>
        <span>02</span>
        <h2>风险规则</h2>
        <p>后续接入 ROI、持续时间与多事件共现判定。</p>
      </article>
      <article>
        <span>03</span>
        <h2>闭环许可</h2>
        <p>后续接入申请、核验、监护、撤销与整改复核。</p>
      </article>
    </section>
  </main>
</template>
