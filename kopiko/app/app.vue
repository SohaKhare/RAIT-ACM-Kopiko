<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { LANGUAGES, simulateGeminiTranslation, translateCardText } from './utils/gemini'
import DashboardCards from './components/DashboardCards.vue'

// State
const selectedLanguage = ref('en-IN')
const hasSelectedLanguage = ref(false)
const isStarted = ref(false)
const activeStep = ref(-2) // -2: Welcome, -1: Voice Lang Select, 0: Q1, 1: Q2
const isCompleted = ref(false)
const showStatsOverlay = ref(false)
const micState = ref<'idle' | 'listening' | 'processing'>('idle')

const stateName = ref('')
const districtName = ref('')

const questions = ['q1', 'q2']
const userAnswers = ref<string[]>([])

const selectLanguage = (code: string) => {
  selectedLanguage.value = code
  hasSelectedLanguage.value = true
  activeStep.value = 0
  askCurrentQuestion()
}

const startLanguageSelection = () => {
  activeStep.value = -1
  const prompt = "Which language do you prefer? English, हिंदी, मराठी, اردو, தமிழ்"
  displayText.value = prompt
  speakText(prompt, 'en-IN') // Speak the English part
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
const displayText = ref('Welcome to Kopiko')
const transcript = ref('')

// Location
const userLocation = ref<{ lat: number; lng: number } | null>(null)

// Ask for GPS location
const requestLocation = () => {
  if ('geolocation' in navigator) {
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        userLocation.value = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        }
        console.log('Location retrieved:', userLocation.value)
        try {
          const res = await fetch(`http://localhost:4001/location`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: position.coords.latitude, lng: position.coords.longitude })
          })
          const data = await res.json()
          if (data) {
            stateName.value = data.state || ''
            districtName.value = data.district || data.city || ''
            console.log('Geocoding from backend:', data)
            
            // Save to localStorage
            localStorage.setItem('userLat', position.coords.latitude.toString())
            localStorage.setItem('userLng', position.coords.longitude.toString())
            localStorage.setItem('userState', stateName.value)
            localStorage.setItem('userDistrict', districtName.value)
          }
        } catch(e) {
          console.error('Backend location error:', e)
        }
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

const mediaRecorder = ref<MediaRecorder | null>(null)
const audioChunks = ref<Blob[]>([])

const startListening = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder.value = new MediaRecorder(stream)
    audioChunks.value = []

    mediaRecorder.value.onstart = () => {
      micState.value = 'listening'
      transcript.value = ''
      displayText.value = 'Listening... (Tap mic again to stop)'
    }

    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data)
      }
    }

    mediaRecorder.value.onstop = async () => {
      micState.value = 'processing'
      displayText.value = 'Processing...'
      const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })
      
      const formData = new FormData()
      formData.append('file', audioBlob, 'recording.webm')
      
      const lang = activeStep.value === -1 ? 'en-IN' : selectedLanguage.value
      formData.append('language', lang)
      formData.append('lat', localStorage.getItem('userLat') || '0')
      formData.append('lng', localStorage.getItem('userLng') || '0')
      formData.append('state', localStorage.getItem('userState') || '')
      formData.append('district', localStorage.getItem('userDistrict') || '')

      try {
        const res = await fetch(`http://localhost:4001/llm/audio`, {
          method: 'POST',
          body: formData
        })
        const data = await res.json()
        console.log('LLM Audio response:', data)
        
        const aiResponse = data.reply_text || 'Completed'
        transcript.value = aiResponse
        displayText.value = aiResponse
        
        if (activeStep.value === -1) {
           const lower = aiResponse.toLowerCase()
           if (lower.includes('hindi')) selectLanguage('hi-IN')
           else if (lower.includes('marathi')) selectLanguage('mr-IN')
           else if (lower.includes('urdu')) selectLanguage('ur-IN')
           else if (lower.includes('tamil')) selectLanguage('ta-IN')
           else selectLanguage('en-IN') // default
           micState.value = 'idle'
           return
        }
        
        userAnswers.value.push(aiResponse)
        
        micState.value = 'idle'
        transcript.value = ''
        
        // Move to next step
        if (activeStep.value < questions.length - 1) {
          activeStep.value++
          askCurrentQuestion()
        } else {
          isCompleted.value = true
          showStatsOverlay.value = true // Automatically show stats
          
          const helloText = translateCardText('hello', selectedLanguage.value)
          const swipeDownText = translateCardText('swipe_down', selectedLanguage.value)
          displayText.value = helloText
          speakText(`${helloText}. ${swipeDownText}`, selectedLanguage.value)
        }
        
      } catch (e) {
        console.error('LLM Audio error:', e)
        displayText.value = 'Error processing audio. Try again.'
        micState.value = 'idle'
      }
      
      // Stop tracks to release mic
      stream.getTracks().forEach(track => track.stop())
    }

    mediaRecorder.value.start()
  } catch (err) {
    console.error('Microphone access denied or error:', err)
    alert('Please allow microphone access to use voice features.')
  }
}

const stopListening = () => {
  if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
    mediaRecorder.value.stop()
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

const handleMandiSelect = (e: any) => {
  const val = e.target.value
  if (val) {
    userAnswers.value.push(val)
    if (activeStep.value < questions.length - 1) {
      activeStep.value++
      askCurrentQuestion()
    } else {
      isCompleted.value = true
      showStatsOverlay.value = true // Automatically show stats
      const helloText = translateCardText('hello', selectedLanguage.value)
      const swipeDownText = translateCardText('swipe_down', selectedLanguage.value)
      displayText.value = helloText
      speakText(`${helloText}. ${swipeDownText}`, selectedLanguage.value)
    }
  }
}

const handleSpeakClick = () => {
  if (activeStep.value === -2) {
    startLanguageSelection()
  } else if (!isStarted.value && activeStep.value > -1) {
    askCurrentQuestion()
  } else if (micState.value === 'idle') {
    startListening()
  } else if (micState.value === 'listening') {
    stopListening()
  }
}

</script>

<template>
  <div class="app-container">
    <!-- Initial Start Screen (Since browsers require click for audio) -->
    <template v-if="activeStep === -2">
      <div class="language-selection-screen">
        <h1 class="welcome-title">Welcome to Kopiko</h1>
        <button @click="startLanguageSelection" class="big-lang-btn">
          Start Voice Assistant
        </button>
      </div>
    </template>

    <!-- Main App Interface -->
    <template v-else>
      <!-- Header with Language Selector -->
      <header class="top-bar">
        <div class="logo">Kopiko</div>
        <div style="display:flex; gap:10px; align-items:center;">
          <select v-model="selectedLanguage" class="custom-select language-dropdown" @change="askCurrentQuestion" style="text-align: center; text-align-last: center;">
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
          
          <!-- Mandi Dropdown Fallback (Shows only for 1st question) -->
          <div v-if="isStarted && activeStep === 0 && !isCompleted && districtName" style="margin-top: 2rem; z-index: 60; width: 100%; display: flex; justify-content: center;">
            <select @change="handleMandiSelect" class="custom-select well-dropdown" style="text-align: center; text-align-last: center;">
               <option disabled selected value="">{{ translateCardText('select_mandi', selectedLanguage) }}</option>
               <option v-for="mandi in ['mandi_alpha', 'mandi_beta', 'mandi_gamma']" :key="mandi" :value="mandi">
                 {{ translateCardText(mandi, selectedLanguage) }} {{ districtName ? ` - ${districtName}` : '' }}
               </option>
            </select>
          </div>
        </div>

        <!-- Stats Overlay (Slides up like an app drawer) -->
        <Transition name="slide-up">
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
        </Transition>
      </main>

      <!-- Bottom Controls (ALWAYS ON TOP) -->
      <footer class="bottom-controls">
        <div style="display:flex; flex-direction:column; gap:10px; width:100%; max-width:400px; align-items:center;">
          
          <div v-if="isCompleted && !showStatsOverlay" class="swipe-up-indicator blink">
            <span>{{ translateCardText('swipe_up', selectedLanguage) }}</span>
          </div>

          <button 
            class="speak-btn"
            :class="`mic-${micState}`"
            @click="handleSpeakClick"
            :disabled="micState === 'processing'"
          >
            <span v-if="micState === 'idle' && activeStep === -1">🎤 Select Language</span>
            <span v-else-if="micState === 'idle'">🎤 Speak</span>
            <span v-else-if="micState === 'listening'">⏹️ Stop Recording</span>
            <span v-else>Processing...</span>
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

/* Enhanced Dropdown Styles */
.custom-select {
  appearance: none;
  background-color: rgba(245, 245, 220, 0.4); /* Glassy beige */
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: #2e3b32; /* Darker text for beige background */
  border: 1px solid rgba(245, 245, 220, 0.6);
  border-radius: 0.75rem;
  outline: none;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transition: all 0.3s ease;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%232e3b32%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 0.75rem top 50%;
  background-size: 0.65rem auto;
}

.custom-select:hover, .custom-select:focus {
  background-color: rgba(245, 245, 220, 0.6);
  border-color: rgba(245, 245, 220, 0.9);
  box-shadow: 0 6px 16px rgba(0,0,0,0.1);
}

.language-dropdown {
  padding: 0.5rem 2rem 0.5rem 1rem;
  font-size: 0.95rem;
  font-weight: 500;
}

.well-dropdown {
  padding: 0.75rem 2.5rem 0.75rem 1.25rem;
  font-size: 1.1rem;
  font-weight: 600;
  width: 100%;
  max-width: 350px;
}

.custom-select option {
  background-color: var(--bg-main);
  color: var(--text-primary);
  font-weight: 500;
  padding: 0.5rem;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 1.5rem;
  height: 70vh; /* roughly 70-80% of screen */
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
  z-index: 10;
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
  margin: 0;
  word-wrap: break-word;
  text-align: center;
}

.status-text {
  margin-top: 0.75rem;
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

/* Bottom Controls Pinned to Bottom */
.bottom-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 20vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1.5rem;
  background: transparent;
  z-index: 50; /* Above overlay */
  pointer-events: none; /* Let clicks pass through empty spaces */
}

.bottom-controls > div {
  pointer-events: auto; /* Re-enable clicks on the buttons container */
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

/* Stats Overlay App Drawer Style */
.stats-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 80vh; /* Slides up 80% of screen */
  padding: 1rem;
  padding-bottom: 25vh; /* enough space so bottom cards aren't hidden behind speak btn */
  overflow-y: auto;
  background: transparent; /* TRANSPARENT BACKGROUND AS REQUESTED */
  z-index: 20; /* Underneath bottom-controls (50) */
}

/* App Drawer Animation */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
}
</style>
