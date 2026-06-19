<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { LANGUAGES, simulateGeminiTranslation, translateCardText } from './utils/gemini'
import DashboardCards from './components/DashboardCards.vue'

// State
const selectedLanguage = ref('en-IN')
const hasSelectedLanguage = ref(false)
const isStarted = ref(false)
const activeStep = ref(0)
const isCompleted = ref(false)
const showStatsOverlay = ref(false)
const micState = ref<'idle' | 'listening' | 'processing'>('idle')

const selectLanguage = (code: string) => {
  selectedLanguage.value = code
  hasSelectedLanguage.value = true
  askCurrentQuestion()
}

// Touch handling for swipe up to show cards
const touchStartY = ref(0)
const handleTouchStart = (e: TouchEvent) => {
  touchStartY.value = e.touches[0].clientY
}
const handleTouchEnd = (e: TouchEvent) => {
  const touchEndY = e.changedTouches[0].clientY
  if (touchStartY.value - touchEndY > 50) {
    if (isCompleted.value && !showStatsOverlay.value) {
      showStatsOverlay.value = true
      speakText(translateCardText('stats_speech', selectedLanguage.value), selectedLanguage.value)
    }
  } else if (touchEndY - touchStartY.value > 50) {
    showStatsOverlay.value = false
  }
}

// Text content
const displayText = ref('Select your language and press Speak to start.')
const transcript = ref('')

const questions = ['q1', 'q2']
const userAnswers = ref<string[]>([])

// Location
const userLocation = ref<{ lat: number; lng: number } | null>(null)

// Ask for GPS location
const requestLocation = () => {
  if ('geolocation' in navigator) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        userLocation.value = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        }
        console.log('Location retrieved:', userLocation.value)
      },
      (error) => {
        console.error('Error getting location', error)
      }
    )
  }
}

onMounted(() => {
  requestLocation()
})

const speakText = (text: string, lang: string) => {
  if (!('speechSynthesis' in window)) return

  window.speechSynthesis.cancel() // clear queue
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = lang
  window.speechSynthesis.speak(utterance)
}

const startListening = () => {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    alert('Speech recognition is not supported in this browser.')
    return
  }

  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  const recognition = new SpeechRecognition()
  
  recognition.lang = selectedLanguage.value
  recognition.interimResults = true
  recognition.maxAlternatives = 1

  recognition.onstart = () => {
    micState.value = 'listening'
    transcript.value = ''
  }

  recognition.onresult = (event: any) => {
    const current = event.resultIndex
    const result = event.results[current][0].transcript
    transcript.value = result
    displayText.value = result // Show what they are saying in the big text area
  }

  recognition.onerror = (event: any) => {
    console.error('Speech recognition error', event.error)
    micState.value = 'idle'
  }

  recognition.onend = async () => {
    micState.value = 'processing'
    
    // Simulate getting translation/backend processing
    await new Promise(resolve => setTimeout(resolve, 800))
    
    userAnswers.value.push(transcript.value || 'Dummy answer')
    
    micState.value = 'idle'
    transcript.value = ''
    
    // Move to next step
    if (activeStep.value < questions.length - 1) {
      activeStep.value++
      askCurrentQuestion()
    } else {
      isCompleted.value = true
      const helloText = translateCardText('hello', selectedLanguage.value)
      const swipeUpText = translateCardText('swipe_up', selectedLanguage.value)
      displayText.value = helloText
      speakText(`${helloText}. ${swipeUpText}`, selectedLanguage.value)
    }
  }

  recognition.start()
}

const runDemo = async () => {
  if (isCompleted.value) return
  micState.value = 'listening'
  
  const dummyTexts = ["Kalyan Mandi", "Wheat"]
  const currentAnswer = dummyTexts[activeStep.value] || "Dummy Answer"
  
  // Simulate typing it out slowly as if transcribed live
  transcript.value = ""
  for (let i = 0; i < currentAnswer.length; i++) {
    await new Promise(r => setTimeout(r, 100))
    transcript.value += currentAnswer[i]
    displayText.value = transcript.value
  }
  
  await new Promise(r => setTimeout(r, 800))
  
  micState.value = 'processing'
  await new Promise(resolve => setTimeout(resolve, 800))
  
  userAnswers.value.push(transcript.value)
  micState.value = 'idle'
  transcript.value = ''
  
  if (activeStep.value < questions.length - 1) {
    activeStep.value++
    askCurrentQuestion()
  } else {
    isCompleted.value = true
    const helloText = translateCardText('hello', selectedLanguage.value)
    const swipeUpText = translateCardText('swipe_up', selectedLanguage.value)
    displayText.value = helloText
    speakText(`${helloText}. ${swipeUpText}`, selectedLanguage.value)
  }
}

const askCurrentQuestion = async () => {
  isStarted.value = true
  displayText.value = 'Translating...'
  
  const questionKey = questions[activeStep.value]
  const translatedQuestion = await simulateGeminiTranslation(questionKey, selectedLanguage.value)
  
  displayText.value = translatedQuestion
  speakText(translatedQuestion, selectedLanguage.value)
}

const handleSpeakClick = () => {
  if (isCompleted.value) return
  
  if (!isStarted.value) {
    askCurrentQuestion()
  } else if (micState.value === 'idle') {
    startListening()
  }
}

</script>

<template>
  <div class="app-container">
    <!-- Big Initial Language Selector -->
    <template v-if="!hasSelectedLanguage">
      <div class="language-selection-screen">
        <h1 class="welcome-title">Select Your Language</h1>
        <div class="lang-grid">
          <button 
            v-for="lang in LANGUAGES" 
            :key="lang.code" 
            @click="selectLanguage(lang.code)"
            class="big-lang-btn"
          >
            {{ lang.name }}
          </button>
        </div>
      </div>
    </template>

    <!-- Main App Interface -->
    <template v-else>
      <!-- Header with Language Selector -->
      <header class="top-bar">
        <div class="logo">Kopiko</div>
        <div style="display:flex; gap:10px; align-items:center;">
          <select v-model="selectedLanguage" class="language-dropdown" @change="askCurrentQuestion">
            <option v-for="lang in LANGUAGES" :key="lang.code" :value="lang.code">
              {{ lang.name }}
            </option>
          </select>
        </div>
      </header>

      <!-- Main Content Area -->
      <main class="main-content" @touchstart="handleTouchStart" @touchend="handleTouchEnd">
        <!-- Question / Transcription Area -->
        <div class="text-display-area" :class="{ 'blur-bg': showStatsOverlay }">
          <h1 class="main-text">{{ displayText }}</h1>
          <p v-if="micState === 'listening'" class="status-text blink">Listening...</p>
          <p v-if="micState === 'processing'" class="status-text processing">Processing...</p>
        </div>

        <!-- Stats Overlay -->
        <div v-if="showStatsOverlay" class="stats-overlay">
          <div class="swipe-down-indicator blink">
            <span>{{ translateCardText('swipe_down', selectedLanguage) }}</span>
          </div>
          <DashboardCards 
            :mandi="userAnswers[0] || 'Local Market'" 
            :crop="userAnswers[1] || 'Wheat'" 
            :lang="selectedLanguage"
          />
        </div>
      </main>

      <!-- Bottom Controls -->
      <footer class="bottom-controls" v-if="hasSelectedLanguage && !showStatsOverlay">
        <div style="display:flex; flex-direction:column; gap:10px; width:100%; max-width:400px; align-items:center;">
          
          <div v-if="isCompleted" class="swipe-up-indicator blink">
            <span>{{ translateCardText('swipe_up', selectedLanguage) }}</span>
          </div>

          <button 
            class="speak-btn"
            :class="`mic-${micState}`"
            @click="handleSpeakClick"
            :disabled="micState === 'processing'"
          >
            <span v-if="!isStarted">Start</span>
            <span v-else-if="micState === 'idle'">🎤 Speak</span>
            <span v-else-if="micState === 'listening'">Listening...</span>
            <span v-else>Processing</span>
          </button>
          
          <button v-if="isStarted && micState === 'idle' && !isCompleted" @click="runDemo" class="demo-btn">
            ▶️ Auto Demo
          </button>
        </div>
      </footer>
    </template>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background-color: var(--bg-main);
  color: var(--text-primary);
  overflow: hidden;
  position: relative;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  height: 10vh;
}

.logo {
  font-weight: 700;
  font-size: 1.25rem;
  color: var(--text-primary);
}

.language-dropdown {
  background-color: transparent;
  color: var(--text-primary);
  border: 1px solid var(--text-primary);
  border-radius: 0.5rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.9rem;
  outline: none;
}

.language-dropdown option {
  background-color: var(--bg-main);
  color: var(--text-primary);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 1.5rem;
  height: 70vh; /* roughly 70-80% of screen */
  overflow-y: auto;
  position: relative;
}

.text-display-area {
  width: 100%;
  max-width: 600px;
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  transition: opacity 0.3s ease;
}

.blur-bg {
  opacity: 0.1;
  pointer-events: none;
}

.main-text {
  font-size: 2rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  word-wrap: break-word;
}

.status-text {
  margin-top: 1.5rem;
  font-size: 1.1rem;
  color: var(--accent-green);
}

.blink {
  animation: blinker 1.5s linear infinite;
}

.swipe-up-indicator {
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--accent-green);
}

.swipe-down-indicator {
  text-align: center;
  margin-bottom: 1rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--accent-green);
}

@keyframes blinker {
  50% { opacity: 0; }
}

.bottom-controls {
  height: 20vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1.5rem;
  background: linear-gradient(to top, var(--bg-main) 0%, transparent 100%);
  z-index: 10; /* Prevent swipe-up obstruction */
}

.speak-btn {
  width: 100%;
  max-width: 400px;
  height: 64px;
  border-radius: 9999px; /* pill shaped */
  border: none;
  background-color: var(--mic-idle);
  color: white;
  font-size: 1.25rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;
}

.speak-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.demo-btn {
  background: transparent;
  color: var(--text-primary);
  border: 1px solid var(--text-primary);
  border-radius: 9999px;
  padding: 0.5rem 1rem;
  font-size: 1rem;
  cursor: pointer;
}

/* Big Language Screen Styles */
.language-selection-screen {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100%;
  padding: 2rem;
}

.welcome-title {
  font-size: 2.5rem;
  color: var(--text-primary);
  margin-bottom: 3rem;
  text-align: center;
  font-weight: 700;
}

.lang-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
  width: 100%;
  max-width: 400px;
}

.big-lang-btn {
  background-color: var(--card-bg);
  color: var(--text-card);
  border: none;
  border-radius: 1rem;
  padding: 1.5rem;
  font-size: 1.5rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  transition: transform 0.2s;
}

.big-lang-btn:active {
  transform: scale(0.98);
}

/* Stats Overlay */
.stats-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  padding: 1rem;
  background: var(--bg-main);
  box-shadow: 0 -4px 10px rgba(0,0,0,0.05);
  border-top-left-radius: 1.5rem;
  border-top-right-radius: 1.5rem;
  z-index: 20;
}
</style>
