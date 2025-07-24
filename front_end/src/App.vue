<!-- Vite + Vue3 + TailwindCSS 示例上传组件 UI -->
<template>
  <div class="min-h-screen w-screen overflow-x-hidden bg-[#cccccc] flex items-center justify-center px-4">
    <div class="w-full max-w-md bg-white rounded-2xl shadow-xl p-10 flex flex-col justify-center">
      <h2 class="text-3xl font-bold mb-6 text-gray-800 text-center">📄 上传论文链接</h2>

      <label for="url" class="block text-sm font-medium text-gray-700 mb-2 text-center">
        输入包含 PDF 的网页链接：
      </label>

      <input
        v-model="url"
        type="url"
        id="url"
        placeholder="https://example.com/papers"
        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-black placeholder-gray-400 mb-6"
      />

      <button
        @click="handleSubmit"
        class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl transition"
        :disabled="loading || !url"
      >
        {{ loading ? '提交中...' : '提交链接' }}
      </button>

      <div v-if="message" class="mt-6 text-sm text-green-600 text-center">
        {{ message }}
      </div>
    </div>
  </div>
</template>


<script setup>
import { ref } from 'vue'

const url = ref('')
const loading = ref(false)
const message = ref('')

const handleSubmit = async () => {
  if (!url.value) return
  loading.value = true
  message.value = ''

  try {
    const res = await fetch('/api/upload-url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url.value })
    })

    const data = await res.json()
    message.value = data.message || '提交成功！后台已开始处理。'
  } catch (err) {
    console.error(err)
    message.value = '提交失败，请检查链接或稍后重试。'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
body {
  font-family: 'Inter', sans-serif;
}
</style>

