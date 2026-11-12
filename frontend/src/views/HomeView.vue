<!-- frontend/src/views/HomeView.vue -->
<script setup>
import { ref, nextTick } from 'vue'  // 确保导入 nextTick
import axios from 'axios'
import { ElMessage, ElLoading } from 'element-plus'
import { Upload} from '@element-plus/icons-vue'
import MaskEditor from '@/components/MaskEditor.vue'
const logoUrl = new URL('@/assets/images/C.png', import.meta.url).href
// 🔹 当前模式状态，0 代表初始选中"草图转绘"
const currentMode = ref(0)
const maskPreviewContainer = ref(null)
const inputPreviewUrl = ref('')
const maskPreviewUrl = ref('')
const outputUrl = ref('')
const promptText = ref('')
const isGenerating = ref(false)
const showMaskEditor = ref(false)

const modes = [
  { id: 0, name: '草图转绘', emoji: '🖌️', endpoint: '/api/v1/generation/sketch' },
  { id: 1, name: '局部重绘', emoji: '🎨', endpoint: '/api/v1/generation/inpainting' },
  { id: 2, name: '背景转换', emoji: '🌄', endpoint: '/api/v1/generation/background' },
  { id: 3, name: '文生图',   emoji: '📝', endpoint: '/api/v1/generation/text2image' }
]

const stylePresets = [
  {
    name: '水墨风格',
    prompt: 'masterpiece, best quality, traditional chinese ink painting, sumi-e, ink wash painting, elegant brush strokes, monochrome, minimalist composition, negative space, artistic, serene atmosphere, (subject)'
  },
  {
    name: '彩铅风格',
    prompt: 'masterpiece, best quality, colored pencil drawing, professional colored pencil illustration, layered pencil strokes, visible pencil texture, cross-hatching, soft blending, detailed shading, vibrant colors, paper texture, realistic pencil marks, hand-drawn, delicate lines, (subject), artistic, highly detailed'
  },
  {
    name: '霓虹光影',
    prompt: 'masterpiece, best quality, neon lights, cyberpunk style, vibrant colors, glowing effects, dramatic lighting, futuristic atmosphere, high contrast, detailed illustration, (subject), cinematic, stunning visuals'
  },
  {
    name: '油画风格',
    prompt: 'masterpiece, best quality, oil painting, traditional oil on canvas, thick impasto texture, visible brush strokes, rich color depth, dramatic lighting, museum quality, (subject), artistic, classical, highly detailed'
  },
  {
    name: '素描风格',
    prompt: 'masterpiece, best quality, pencil sketch, detailed graphite drawing, realistic pencil texture, cross hatching, shading, paper texture, monochrome, hand-drawn, fine lines, (subject), artistic, professional illustration'
  },
  {
    name: '水粉风格',
    prompt: 'masterpiece, best quality, gouache painting, opaque watercolor, matte finish, rich pigment, visible brushwork, soft blending, paper texture, vibrant yet soft colors, (subject), artistic, illustrative'
  },
  {
    name: '动漫风格',
    prompt: 'masterpiece, best quality, anime style, detailed anime illustration, beautiful anime key visual, vibrant colors, sharp lines, expressive eyes, dynamic composition, (subject), studio ghibli or kyoto animation quality'
  },
  {
    name: '写实风格',
    prompt: 'masterpiece, best quality, photorealistic, ultra realistic, extremely detailed, 8k, raw photo, cinematic lighting, sharp focus, intricate details, (subject), national geographic style'
  }
]

const historyList = ref([])

const handleFileUpload = (uploadFile) => {
  const file = uploadFile.raw || uploadFile
  if (!file || !['image/png', 'image/jpeg'].includes(file.type)) {
    ElMessage.error('仅支持 PNG 和 JPG 格式')
    return false
  }

  if (inputPreviewUrl.value) URL.revokeObjectURL(inputPreviewUrl.value)

  inputPreviewUrl.value = URL.createObjectURL(file)
  outputUrl.value = ''

  addToHistory(file)
  ElMessage.success('上传成功')
  return false
}

const addToHistory = (file) => {
  const url = URL.createObjectURL(file)
  historyList.value.unshift({ id: Date.now(), url, name: file.name })
  if (historyList.value.length > 20) {
    URL.revokeObjectURL(historyList.value.pop().url)
  }
}

const loadFromHistory = (item) => {
  inputPreviewUrl.value = item.url
  ElMessage.info('已加载历史图片')
}

const openMaskEditor = () => {
  if (!inputPreviewUrl.value) {
    ElMessage.warning('图片为空，请先上传图片')
    return
  }
  showMaskEditor.value = true
}

const generateImage = async () => {
  if (!inputPreviewUrl.value && currentMode.value !== 3) {
    ElMessage.warning('请先上传图片(文生图除外)')
    return
  }
  if (!maskPreviewUrl.value && currentMode.value == 1) {
    ElMessage.warning('请先编辑遮罩')
    return
  }
  isGenerating.value = true
  const loading = ElLoading.service({ fullscreen: true, text: '生成中...' })

  const formData = new FormData()

  try {
    if (inputPreviewUrl.value) {
      // 从预览URL转换为 Blob
      const response = await fetch(inputPreviewUrl.value)
      const blob = await response.blob()
      formData.append('image', blob, 'input.png')   // 统一使用 'image'
    }

    if (currentMode.value === 1 && maskPreviewUrl.value) {
      const maskResponse = await fetch(maskPreviewUrl.value)
      const maskBlob = await maskResponse.blob()
      formData.append('mask', maskBlob, 'mask.png')
    }

    if (promptText.value) {
      formData.append('prompt', promptText.value)
    }
    const endpoint = modes[currentMode.value].endpoint

    const res = await axios.post(endpoint, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (res.data.code === 200 && res.data.data?.output_url) {
      outputUrl.value = res.data.data.output_url
      addGeneratedResultToHistory(outputUrl.value)
      ElMessage.success('生成成功！')
    } else {
      ElMessage.error(res.data.msg || '生成失败')
    }
  } catch (err) {
    ElMessage.error('请求失败')
  } finally {
    isGenerating.value = false
    loading.close()
  }
}
const addGeneratedResultToHistory = async (generatedUrl) => {
  try {
    const response = await fetch(generatedUrl)
    const blob = await response.blob()

    // 创建一个 File 对象（兼容 addToHistory）
    const generatedFile = new File([blob], `生成_${Date.now()}.png`, { type: 'image/png' })

    // 调用你现有的 addToHistory 函数
    addToHistory(generatedFile)

    console.log('✅ 生成结果已加入历史记录')
  } catch (err) {
    console.error('添加生成结果到历史失败:', err)
  }
}
const downloadImage = async () => {
  if (!outputUrl.value) {
    ElMessage.warning('没有可下载的图片')
    return
  }

  try {
    // 如果是相对路径，补全为完整 URL
    let fullUrl = outputUrl.value
    if (fullUrl.startsWith('/')) {
      fullUrl = `http://127.0.0.1:8000${fullUrl}`
    }

    console.log('下载地址:', fullUrl)

    // 使用 fetch + blob 的方式下载（更稳定）
    const response = await fetch(fullUrl)
    if (!response.ok) throw new Error('下载失败')

    const blob = await response.blob()
    const blobUrl = URL.createObjectURL(blob)

    const a = document.createElement('a')
    a.href = blobUrl
    a.download = `生成结果_${Date.now()}.png`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)

    // 清理内存
    URL.revokeObjectURL(blobUrl)

    ElMessage.success('✅ 图片已下载')
  } catch (err) {
    console.error('下载失败:', err)
    ElMessage.error('下载失败，请右键图片手动保存')
  }
}

const handleMaskConfirm = (maskData) => {
  // 兼容旧版：直接返回 base64 字符串的情况
  if (typeof maskData === 'string' && maskData.startsWith('data:image')) {
    maskPreviewUrl.value = maskData
    ElMessage.success('✅ 遮罩已应用')
    return
  }

  // 新版：处理 {composite, maskOnly} 对象
  if (maskData && typeof maskData === 'object') {
    // 方案A：使用纯遮罩层（透明背景+黑色区域），叠加效果更清晰
    if (maskData.maskOnly) {
      maskPreviewUrl.value = maskData.maskOnly
      ElMessage.success('✅ 纯遮罩层已应用')
    }
    // 方案B：使用合成预览图（原图+灰色遮罩），视觉反馈更直观
    else if (maskData.composite) {
      maskPreviewUrl.value = maskData.composite
      ElMessage.success('✅ 遮罩预览已应用')
    }
    else {
      console.warn('⚠️ 遮罩数据缺少有效字段:', maskData)
      ElMessage.warning('遮罩数据格式异常')
      return
    }

    // 强制触发视图更新（解决部分浏览器缓存问题）
    nextTick(() => {
      if (maskPreviewContainer.value) {
        maskPreviewContainer.value.style.opacity = '0'
        setTimeout(() => {
          maskPreviewContainer.value.style.opacity = '1'
        }, 50)
      }
    })
  } else {
    console.warn('⚠️ 遮罩数据类型异常:', typeof maskData, maskData)
    ElMessage.error('遮罩加载失败')
  }
}

// 🔹 新增：清除遮罩功能
const clearMask = () => {
  maskPreviewUrl.value = ''
  ElMessage.info('遮罩已清除')
}

const applyStylePreset = (prompt) => {
  promptText.value = prompt
  ElMessage.success('风格已应用')
}
</script>

<template>
  <div class="p-8 max-w-7xl mx-auto">
    <el-row :gutter="24">
      <!-- 最左侧历史记录栏 -->
      <el-col :span="4">
        <el-card shadow="hover" class="h-full">
          <template #header>
            <div class="font-semibold">🕒 近期图像</div>
          </template>
          <div class="space-y-4 max-h-[620px] overflow-y-auto pr-2">
            <div
              v-for="item in historyList"
              :key="item.id"
              @click="loadFromHistory(item)"
              class="cursor-pointer"
            >
              <div class="history-thumb">
                <img :src="item.url" alt="" />
              </div>
            </div>
            <div v-if="historyList.length === 0" class="text-center py-12 text-gray-400">
              暂无历史记录
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 中间：上传区域 -->
      <el-col :span="10">
        <el-card shadow="hover" class="h-full">
          <template #header>
            <div class="flex justify-between items-center">
              <h3 class="text-2xl font-semibold">📤上传图像</h3>
              <el-button
                size="small"
                type="primary"
                @click="openMaskEditor"
              >
                ✏️ 编辑遮罩
              </el-button>
            </div>
          </template>

          <el-upload
            drag
            :auto-upload="false"
            :on-change="handleFileUpload"
            :show-file-list="false"
            accept=".jpg,.jpeg,.png"
            class="upload-zone"
          >
            <div v-if="!inputPreviewUrl" class="upload-placeholder">
              <el-icon size="70" color="#409eff"><Upload /></el-icon>
              <p class="mt-6 text-xl">拖拽或点击上传你的简笔画</p>
              <p class="text-gray-500 mt-3">仅支持 JPG / PNG 格式</p>
            </div>

            <div v-else class="preview-container">
              <img
                :src="inputPreviewUrl"
                alt="预览图"
                class="preview-image"
                draggable="false"
              />
              <img
                v-if="maskPreviewUrl"
                ref="maskPreviewContainer"
                :src="maskPreviewUrl"
                class="preview-mask"
                draggable="false"
                alt="遮罩"
              />
              <el-button
                v-if="maskPreviewUrl"
                size="small"
                type="danger"
                class="mask-clear-btn"
                @click.stop="clearMask"
              >
                ✕ 清除遮罩
              </el-button>
            </div>
          </el-upload>
        </el-card>
      </el-col>

      <!-- 右侧：模式切换 + 提示词 + 生成 -->
      <el-col :span="10">
        <el-card shadow="hover">
          <template #header>
            <!-- 🔹 修改：模式按钮改用 el-button，样式与"开始生成"统一 -->
            <div class="flex gap-2">
              <el-button
                v-for="(mode, i) in modes"
                :key="i"
                :type="currentMode === i ? 'primary' : 'default'"
                size="large"
                class="mode-btn flex-1 text-base font-semibold"
                @click="currentMode = i"
              >
                {{ mode.emoji }} {{ mode.name }}
              </el-button>
            </div>

            <!-- 风格预设按钮行 -->
            <div class="flex gap-2 mt-4 flex-wrap">
              <el-button
                v-for="(style, index) in stylePresets"
                :key="index"
                size="small"
                @click="applyStylePreset(style.prompt)"
                class="style-btn"
              >
                {{ style.name }}
              </el-button>
            </div>
          </template>

          <!-- 可选提示词 -->
          <el-input
            v-model="promptText"
            type="textarea"
            :rows="3"
            placeholder="可选提示词（可不填）"
            class="mt-6"
          />

          <el-button
            type="primary"
            size="large"
            class="w-full mt-8 h-14 text-lg font-semibold"
            :loading="isGenerating"
            @click="generateImage"
          >
            🚀 开始生成
          </el-button>
        </el-card>

        <!-- 生成结果 -->
        <el-card shadow="hover" class="mt-8">
          <template #header>
            <div class="flex justify-between items-center">
              <h3 class="text-xl font-semibold">🎉 生成结果</h3>
              <el-button
                type="primary"
                size="small"
                @click="downloadImage"
              >
                ⬇️ 下载图片
              </el-button>
            </div>
          </template>

          <div class="preview-container result-container">
            <img
              src="/D.png"
              alt="生成结果"
              class="preview-image"
              draggable="false"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <MaskEditor
      v-model="showMaskEditor"
      :image-url="inputPreviewUrl"
      @confirm="handleMaskConfirm"
    />
  </div>
</template>

<style scoped>
.upload-zone {
  border: 3px dashed #d1d5db;
  border-radius: 20px;
}
.upload-zone:hover {
  border-color: #409eff;
}

.preview-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}
.result-container {
  position: relative;
  width: 70%;
  height: 70%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}
.preview-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;           /* 与原图保持一致的对齐方式 */
  pointer-events: none;
  z-index: 2;                    /* 确保在原图上方 */

}
.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.history-thumb {
  width: 100%;
  aspect-ratio: 1 / 1;
  background-color: #27272a;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid transparent;
  transition: all 0.25s ease;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}

.history-thumb:hover {
  border-color: #10b981;
  transform: scale(1.06);
  box-shadow: 0 10px 15px -3px rgb(16 185 129 / 0.3);
}

.history-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* 🔹 新增：模式按钮样式，确保与"开始生成"按钮高度/字体一致 */
.mode-btn {
  height: 3rem !important; /* 与 size="large" 的 el-button 保持一致 */
  border-radius: 8px !important;
}

/* 未选中状态的按钮：浅蓝色背景 + 蓝色文字 */
.mode-btn.el-button--default {
  background-color: #dbeafe !important; /* blue-100 */
  border-color: #93c5fd !important;     /* blue-300 */
  color: #1e40af !important;             /* blue-800 */
}
.mode-btn.el-button--default:hover {
  background-color: #bfdbfe !important; /* blue-200 */
  border-color: #60a5fa !important;     /* blue-400 */
  color: #1e3a8a !important;            /* blue-900 */
}

/* 选中状态的按钮：深蓝色背景（primary 默认样式） */
.mode-btn.el-button--primary {
  background-color: #2563eb !important; /* blue-600 深蓝色 */
  border-color: #2563eb !important;
}

.style-btn {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
}
/* 🔹 新增：遮罩淡入过渡效果 */
.mask-fade-in {
  animation: maskFadeIn 0.3s ease-out forwards;
}

@keyframes maskFadeIn {
  from {
    opacity: 0;
    transform: scale(0.98);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.mask-clear-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

</style>