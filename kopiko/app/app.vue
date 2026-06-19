<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

type LanguageCode = 'en' | 'hi'

const runtimeConfig = useRuntimeConfig()

const selectedLanguage = ref<LanguageCode>('en')
const typedMessage = ref('')
const responseText = ref('')
const statusText = ref('Idle')
const isLoading = ref(false)
const isRecording = ref(false)
const errorMessage = ref('')
const mediaRecorder = ref<MediaRecorder | null>(null)
const recordedChunks = ref<Blob[]>([])
const recordedMimeType = ref('audio/webm')

const apiBase = computed(() => runtimeConfig.public.apiBase || 'http://127.0.0.1:8000')
const labels = computed(() => {
  if (selectedLanguage.value === 'hi') {
    return {
      title: 'जलधार परीक्षण',
      subtitle: 'जेम्मा प्रतिक्रिया यहां आते ही दिखेगी',
      idle: 'तैयार',
      loading: 'प्रतिक्रिया बन रही है...',
      recording: 'रिकॉर्डिंग चालू है...',
      placeholder: 'यहाँ सवाल लिखें',
      speak: 'बोलें',
      stop: 'रोकें',
      send: 'भेजें',
      empty: 'जवाब यहाँ दिखेगा',
      connection: 'बैकएंड परीक्षण मोड',
      error: 'कनेक्शन या API त्रुटि',
    }
  }

  return {
    title: 'JalDhar Test',
    subtitle: 'Gemma response appears here as it comes in',
    idle: 'Ready',
    loading: 'Generating response...',
    recording: 'Recording...',
    placeholder: 'Type the farmer question here',
    speak: 'Speak',
    stop: 'Stop',
    send: 'Send',
    empty: 'Response appears here',
    connection: 'Backend test mode',
    error: 'Connection or API error',
  }
})

function setStatus(nextStatus: string) {
  statusText.value = nextStatus
}

function pickRecordingMimeType() {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/ogg;codecs=opus',
    'audio/webm',
    'audio/ogg',
  ]

  for (const candidate of candidates) {
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(candidate)) {
      return candidate
    }
  }

  return ''
}

function extensionFromMimeType(mimeType: string) {
  if (mimeType.includes('ogg')) {
    return 'ogg'
  }
  if (mimeType.includes('mp4')) {
    return 'mp4'
  }
  return 'webm'
}

async function sendTextMessage() {
  const message = typedMessage.value.trim()
  if (!message || isLoading.value) {
    return
  }

  errorMessage.value = ''
  responseText.value = ''
  isLoading.value = true
  setStatus(labels.value.loading)

  try {
    const result = await $fetch<{ reply_text?: string; response?: string }>(
      `${apiBase.value}/llm/text`,
      {
        method: 'POST',
        body: {
          message_text: message,
          language: selectedLanguage.value,
        },
      },
    )

    responseText.value = result.reply_text || result.response || 'No response text returned.'
    typedMessage.value = ''
    setStatus(labels.value.idle)
  }
  catch (error) {
    responseText.value = ''
    errorMessage.value = error instanceof Error ? error.message : labels.value.error
    setStatus(labels.value.error)
  }
  finally {
    isLoading.value = false
  }
}

async function toggleRecording() {
  if (isRecording.value) {
    mediaRecorder.value?.stop()
    return
  }

  errorMessage.value = ''

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const mimeType = pickRecordingMimeType()
    const recorder = mimeType
      ? new MediaRecorder(stream, { mimeType })
      : new MediaRecorder(stream)

    recordedMimeType.value = recorder.mimeType || mimeType || 'audio/webm'
    console.log('Recorder mime type:', recordedMimeType.value)

    recordedChunks.value = []
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        recordedChunks.value.push(event.data)
      }
    }
    recorder.onstop = async () => {
      isRecording.value = false
      stream.getTracks().forEach(track => track.stop())
      await sendAudioMessage()
    }

    mediaRecorder.value = recorder
    recorder.start()
    isRecording.value = true
    setStatus(labels.value.recording)
  }
  catch (error) {
    errorMessage.value = error instanceof Error ? error.message : labels.value.error
    setStatus(labels.value.error)
  }
}

async function sendAudioMessage() {
  if (!recordedChunks.value.length) {
    setStatus(labels.value.idle)
    return
  }

  isLoading.value = true
  responseText.value = ''
  errorMessage.value = ''
  setStatus(labels.value.loading)

  try {
    const mimeType = recordedMimeType.value || 'audio/webm'
    const fileExtension = extensionFromMimeType(mimeType)
    const audioBlob = new Blob(recordedChunks.value, { type: mimeType })
    const formData = new FormData()
    formData.append('file', audioBlob, `farmer-audio.${fileExtension}`)
    formData.append('language', selectedLanguage.value)

    console.log('Uploading audio blob:', {
      mimeType,
      size: audioBlob.size,
      extension: fileExtension,
    })

    const result = await $fetch<{ reply_text?: string; response?: string }>(
      `${apiBase.value}/llm/audio`,
      {
        method: 'POST',
        body: formData,
      },
    )

    responseText.value = result.reply_text || result.response || 'No response text returned.'
    setStatus(labels.value.idle)
  }
  catch (error) {
    responseText.value = ''
    errorMessage.value = error instanceof Error ? error.message : labels.value.error
    setStatus(labels.value.error)
  }
  finally {
    isLoading.value = false
    recordedChunks.value = []
  }
}

onBeforeUnmount(() => {
  mediaRecorder.value?.stream.getTracks().forEach(track => track.stop())
})
</script>

<template>
  <div class="shell">
    <NuxtRouteAnnouncer />

    <main class="phone">
      <header class="topbar">
        <div>
          <p class="eyebrow">{{ labels.connection }}</p>
          <h1 class="title">{{ labels.title }}</h1>
        </div>

        <label class="language-select">
          <span class="sr-only">Language</span>
          <select v-model="selectedLanguage">
            <option value="en">En</option>
            <option value="hi">Hi</option>
          </select>
        </label>
      </header>

      <section class="response-panel">
        <p class="status">{{ statusText }}</p>

        <div class="response-copy">
          <p v-if="responseText">{{ responseText }}</p>
          <p v-else class="placeholder-copy">{{ labels.empty }}</p>
        </div>

        <p v-if="errorMessage" class="error-copy">{{ errorMessage }}</p>
        <p v-else class="subtitle">{{ labels.subtitle }}</p>
      </section>

      <form class="composer" @submit.prevent="sendTextMessage">
        <textarea
          v-model="typedMessage"
          :placeholder="labels.placeholder"
          rows="3"
        />

        <div class="actions">
          <button
            class="mic-button"
            type="button"
            :class="{ active: isRecording }"
            :disabled="isLoading"
            @click="toggleRecording"
          >
            <span class="mic-icon" aria-hidden="true">●</span>
            {{ isRecording ? labels.stop : labels.speak }}
          </button>

          <button
            class="send-button"
            type="submit"
            :disabled="isLoading || !typedMessage.trim()"
          >
            {{ labels.send }}
          </button>
        </div>
      </form>
    </main>
  </div>
</template>

<style scoped>
:global(body) {
  margin: 0;
  min-height: 100vh;
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.08), transparent 32%),
    linear-gradient(180deg, #171717 0%, #090909 100%);
  color: #f3f3f1;
  font-family: "Comic Sans MS", "Trebuchet MS", cursive, sans-serif;
}

:global(*) {
  box-sizing: border-box;
}

.shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 12px;
}

.phone {
  width: min(100%, 490px);
  min-height: calc(100vh - 24px);
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 20px;
  padding: 18px 18px 22px;
  border: 2px solid rgba(240, 240, 240, 0.65);
  border-radius: 28px;
  background: rgba(15, 15, 15, 0.9);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.4);
}

.topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  margin: 0 0 8px;
  color: rgba(255, 255, 255, 0.62);
  font-size: 0.82rem;
  letter-spacing: 0.04em;
}

.title {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
}

.language-select select {
  appearance: none;
  border: 0;
  outline: 0;
  padding: 6px 24px 6px 10px;
  border-radius: 999px;
  background: transparent;
  color: #f4f2ed;
  font: inherit;
  cursor: pointer;
}

.response-panel {
  display: grid;
  align-content: center;
  justify-items: center;
  text-align: center;
  padding: 12px 10px;
}

.status {
  margin: 0 0 18px;
  color: rgba(255, 255, 255, 0.65);
  font-size: 0.95rem;
}

.response-copy {
  max-width: 300px;
  font-size: clamp(1.8rem, 4vw, 2.4rem);
  line-height: 1.22;
}

.response-copy p {
  margin: 0;
  white-space: pre-wrap;
}

.placeholder-copy {
  color: rgba(255, 255, 255, 0.92);
}

.subtitle {
  margin: 18px 0 0;
  color: rgba(255, 255, 255, 0.48);
  font-size: 0.92rem;
}

.error-copy {
  margin: 18px 0 0;
  color: #ff9e9e;
  font-size: 0.92rem;
}

.composer {
  display: grid;
  gap: 14px;
}

.composer textarea {
  width: 100%;
  resize: none;
  border: 1.5px solid rgba(255, 255, 255, 0.24);
  border-radius: 18px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.02);
  color: #f4f2ed;
  font: inherit;
}

.composer textarea::placeholder {
  color: rgba(255, 255, 255, 0.38);
}

.actions {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
}

.mic-button,
.send-button {
  min-height: 58px;
  border-radius: 18px;
  border: 2px solid rgba(240, 240, 240, 0.72);
  background: transparent;
  color: #f4f2ed;
  font: inherit;
  font-size: 1.2rem;
  cursor: pointer;
  transition:
    transform 160ms ease,
    background-color 160ms ease,
    opacity 160ms ease;
}

.mic-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.mic-button.active {
  background: rgba(255, 255, 255, 0.12);
}

.send-button {
  padding: 0 20px;
}

.mic-button:hover,
.send-button:hover {
  transform: translateY(-1px);
}

.mic-button:disabled,
.send-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
  transform: none;
}

.mic-icon {
  font-size: 1.1rem;
  color: #f7d0d0;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 520px) {
  .phone {
    min-height: calc(100vh - 16px);
    padding: 16px 14px 18px;
    border-radius: 24px;
  }

  .actions {
    grid-template-columns: 1fr;
  }

  .response-copy {
    max-width: 260px;
    font-size: clamp(1.6rem, 8vw, 2.2rem);
  }
}
</style>
