<!-- frontend/src/components/MaskEditor.vue -->
<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import { ElMessage, ElSlider } from 'element-plus'

const props = defineProps({
  modelValue: Boolean,
  imageUrl: { type: String, required: true }
})

const emit = defineEmits(['update:modelValue', 'confirm'])

// ===== 状态管理 =====
const visible = ref(props.modelValue)
const canvas = ref(null)
const ctx = ref(null)
const isCanvasReady = ref(false)
const isDrawing = ref(false)
const maskCanvas = ref(null)   // 专门存纯遮罩（白+透明）
const maskCtx = ref(null)

// 画布配置
const canvasWidth = 620
const canvasHeight = 620

// 笔刷配置（10档：10px ~ 100px）
const brushSize = ref(5) // 默认第5档
const brushSizes = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

// 图片缩放信息（用于坐标转换）
const imageDisplayInfo = ref({
  x: 0, y: 0, width: 0, height: 0, ratio: 1
})

// ===== Canvas 初始化 =====
const initCanvasContext = async () => {
  await nextTick()
  if (!canvas.value) return false

  ctx.value = canvas.value.getContext('2d', { willReadFrequently: true })

  // === 新增：创建纯遮罩画布 ===
  maskCanvas.value = document.createElement('canvas')
  maskCanvas.value.width = canvasWidth
  maskCanvas.value.height = canvasHeight
  maskCtx.value = maskCanvas.value.getContext('2d')

  isCanvasReady.value = true
  return true
}

// ===== 图片加载（只绘制原图） =====
const loadImage = (url) => {
  if (!ctx.value) return

  const img = new Image()
  img.crossOrigin = 'anonymous'

  img.onload = () => {
    console.log('✅ 图片加载成功')

    // 清空画布
    ctx.value.clearRect(0, 0, canvasWidth, canvasHeight)

    // 计算等比例缩放参数
    const ratio = Math.min(canvasWidth / img.width, canvasHeight / img.height)
    const w = img.width * ratio
    const h = img.height * ratio
    const x = (canvasWidth - w) / 2
    const y = (canvasHeight - h) / 2

    // 保存显示参数（用于坐标转换）
    imageDisplayInfo.value = { x, y, width: w, height: h, ratio }

    // 绘制原图（无遮罩）
    ctx.value.drawImage(img, x, y, w, h)

    console.log('🖼️ 图片绘制完成，等待用户绘制遮罩')
  }

  img.onerror = () => {
    console.error('❌ 图片加载失败:', url)
    ElMessage.error('图片加载失败，请检查 URL 或 CORS 配置')
  }

  img.src = url
}

// ===== 坐标转换：鼠标事件坐标 → Canvas 坐标 =====
const getCanvasCoords = (e) => {
  if (!canvas.value) return null

  const rect = canvas.value.getBoundingClientRect()
  const scaleX = canvasWidth / rect.width
  const scaleY = canvasHeight / rect.height

  // 支持 mouse 和 touch 事件
  const clientX = e.clientX || (e.touches && e.touches[0]?.clientX)
  const clientY = e.clientY || (e.touches && e.touches[0]?.clientY)

  if (clientX === undefined || clientY === undefined) return null

  return {
    x: (clientX - rect.left) * scaleX,
    y: (clientY - rect.top) * scaleY
  }
}

// ===== 坐标转换：Canvas 坐标 → 图片实际坐标 =====
const canvasToImageCoords = (canvasX, canvasY) => {
  const { x, y, width, height } = imageDisplayInfo.value

  // 判断是否在图片区域内
  if (
    canvasX < x || canvasX > x + width ||
    canvasY < y || canvasY > y + height
  ) {
    return null
  }

  // 转换到图片原始坐标系
  return {
    x: (canvasX - x) / imageDisplayInfo.value.ratio,
    y: (canvasY - y) / imageDisplayInfo.value.ratio
  }
}

// ===== 绘制遮罩（半透明阴影） =====
// 绘制遮罩（同时绘制预览和真实遮罩）
const drawMask = (canvasX, canvasY) => {
  if (!ctx.value || !maskCtx.value) return

  const imgCoords = canvasToImageCoords(canvasX, canvasY)
  if (!imgCoords) return

  const actualBrushSize = brushSizes[brushSize.value - 1] * imageDisplayInfo.value.ratio

  // ===== 1. 在主画布上画预览（给用户看）=====
  ctx.value.globalCompositeOperation = 'source-over'
  ctx.value.beginPath()
  ctx.value.arc(canvasX, canvasY, actualBrushSize / 2, 0, Math.PI * 2)
  ctx.value.fillStyle = 'rgb(255,255,255)'   // 半透明红色，更清晰
  ctx.value.fill()

  // ===== 2. 在 maskCanvas 上画纯白色（用于后端）=====
  maskCtx.value.globalCompositeOperation = 'source-over'
  maskCtx.value.beginPath()
  maskCtx.value.arc(canvasX, canvasY, actualBrushSize / 2, 0, Math.PI * 2)
  maskCtx.value.fillStyle = '#FFFFFF'   // 纯白色
  maskCtx.value.fill()
}

// ===== 鼠标/触摸事件处理 =====
const handleDrawStart = (e) => {
  e.preventDefault()
  const coords = getCanvasCoords(e)
  if (!coords) return

  isDrawing.value = true
  drawMask(coords.x, coords.y)
}

const handleDrawMove = (e) => {
  if (!isDrawing.value) return
  e.preventDefault()

  const coords = getCanvasCoords(e)
  if (!coords) return

  drawMask(coords.x, coords.y)
}

const handleDrawEnd = () => {
  isDrawing.value = false
}

// ===== 状态同步 =====
watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

// 监听 dialog 打开 + imageUrl 变化
watch(
  [() => visible.value, () => props.imageUrl],
  async ([opened, url]) => {
    if (opened && url) {
      await initCanvasContext()
      if (isCanvasReady.value) {
        loadImage(url)
      }
    }
  }
)

const confirmMask = () => {
  if (!canvas.value || !maskCanvas.value) {
    ElMessage.warning('Canvas 未就绪')
    return
  }

  try {
    // 1. 合成预览图（原图 + 红色遮罩）——给用户看
    const compositeBase64 = canvas.value.toDataURL('image/png')

    // 2. 纯遮罩图（透明背景 + 白色遮罩区域）——这是后端真正需要的
    // 先把 maskCanvas 转成带透明背景的图像
    const maskOnlyBase64 = maskCanvas.value.toDataURL('image/png')

    emit('confirm', {
      composite: compositeBase64,   // 前端预览用
      maskOnly: maskOnlyBase64      // 后端 inpainting 用（最重要）
    })

    visible.value = false
    ElMessage.success('✅ 遮罩已生成并应用')

  } catch (e) {
    console.error('❌ 生成遮罩失败:', e)
    ElMessage.error('生成遮罩失败')
  }
}

// ===== 重置遮罩（重新加载原图） =====
const resetMask = () => {
  if (props.imageUrl && ctx.value) {
    loadImage(props.imageUrl)

    // 清空遮罩画布
    if (maskCtx.value) {
      maskCtx.value.clearRect(0, 0, canvasWidth, canvasHeight)
    }

    ElMessage.success('✅ 遮罩已重置')
  }
}

// ===== 生命周期 =====
onMounted(async () => {
  if (visible.value) {
    await initCanvasContext()
  }
})
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="🎨 遮罩编辑器"
    width="880px"
    @update:model-value="visible = $event"
    @opened="initCanvasContext"
  >
    <!-- Canvas 画布 -->
    <canvas
      ref="canvas"
      :width="canvasWidth"
      :height="canvasHeight"
      class="border border-gray-300 mx-auto block cursor-crosshair rounded-2xl shadow-md select-none"
      @mousedown="handleDrawStart"
      @mousemove="handleDrawMove"
      @mouseup="handleDrawEnd"
      @mouseleave="handleDrawEnd"
      @touchstart="handleDrawStart"
      @touchmove="handleDrawMove"
      @touchend="handleDrawEnd"
    />

    <!-- 工具栏：笔刷大小 + 操作按钮 -->
    <div class="mt-4 px-2">
      <!-- 笔刷大小调节 -->
      <div class="flex items-center gap-4 mb-3">
        <span class="text-sm text-gray-600 w-20">🖌️ 笔刷大小:</span>
        <el-slider
          v-model="brushSize"
          :min="1"
          :max="10"
          :step="1"
          :format-tooltip="(val) => `${brushSizes[val - 1]}px`"
          show-stops
          class="flex-1"
        />
        <span class="text-sm font-medium w-16 text-right">
          {{ brushSizes[brushSize - 1] }}px
        </span>
      </div>

      <!-- 操作按钮 -->
      <div class="flex justify-between items-center pt-2 border-t border-gray-100">
        <el-button
          size="small"
          @click="resetMask"
          class="text-gray-600"
        >
          🔄 重置遮罩
        </el-button>
        <div class="text-xs text-gray-400">
          💡 提示：在图片上点击或拖动即可添加遮罩
        </div>
      </div>
    </div>

    <!-- 底部确认按钮 -->
    <template #footer>
      <div class="flex justify-end gap-4">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="confirmMask">✅ 确认遮罩</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
/* 优化 slider 样式 */
:deep(.el-slider__runway) {
  margin-right: 60px;
}
:deep(.el-slider__bar) {
  background-color: #409eff;
}
:deep(.el-slider__button) {
  border: 2px solid #409eff;
}

/* 防止移动端滚动 */
canvas {
  display: block;
  margin: 0 auto;           /* 强制水平居中 */
  max-width: 100%;          /* 防止超出弹窗 */
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  touch-action: none;
  background: #f8fafc;
}
</style>