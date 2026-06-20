<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { LANGUAGES, simulateGeminiTranslation, translateCardText } from './utils/gemini'
import DashboardCards from './components/DashboardCards.vue'

// State
const config = useRuntimeConfig()
const selectedLanguage = ref('en-IN')
const hasSelectedLanguage = ref(false)
const isStarted = ref(false)
const activeStep = ref(-2) // -2: Welcome, -1: Voice Lang Select, 0: Q1, 1: Q2
const isCompleted = ref(false)
const showStatsOverlay = ref(false)
const micState = ref<'idle' | 'listening' | 'processing'>('idle')

const isSplitLayout = computed(() => {
  return (isStarted.value && activeStep.value === 0) || isCompleted.value
})

const stateName = ref('')
const districtName = ref('')
const availableMandis = ref<string[]>(['All Markets'])
const availableStates = ref<string[]>([])
const availableDistricts = ref<string[]>([])

const fetchStatesList = async () => {
  try {
    const res = await fetch(`${config.public.apiBase}/location/states`)
    const data = await res.json()
    if (data && Array.isArray(data.states)) {
      availableStates.value = data.states
    }
  } catch(e) {
    console.error('Error fetching states list:', e)
  }
}

const fetchDistrictsList = async () => {
  if (!stateName.value) {
    availableDistricts.value = []
    return
  }
  try {
    const res = await fetch(`${config.public.apiBase}/location/districts?state=${encodeURIComponent(stateName.value)}`)
    const data = await res.json()
    if (data && Array.isArray(data.districts)) {
      availableDistricts.value = data.districts
    }
  } catch(e) {
    console.error('Error fetching districts list:', e)
  }
}

const fetchAvailableMandis = async () => {
  if (!districtName.value) {
    availableMandis.value = ['All Markets']
    return
  }
  try {
    const mandiRes = await fetch(`${config.public.apiBase}/location/mandis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ district: districtName.value, state: stateName.value })
    })
    const mandiData = await mandiRes.json()
    if (mandiData && Array.isArray(mandiData.mandis)) {
      availableMandis.value = ['All Markets', ...mandiData.mandis]
    }
  } catch(e) {
    console.error('Error fetching mandis:', e)
  }
}

watch(stateName, async (newVal, oldVal) => {
  await fetchDistrictsList()
  farmerContext.value.state_name = stateName.value
  
  if (oldVal && newVal !== oldVal) {
    if (!availableDistricts.value.includes(districtName.value)) {
      districtName.value = ''
      availableMandis.value = ['All Markets']
    }
  }
})

watch(districtName, () => {
  fetchAvailableMandis()
  farmerContext.value.district_name = districtName.value
})

const farmerContext = ref({
  preferred_language: null as string | null,
  state_name: null as string | null,
  district_name: null as string | null,
  current_crop: null as string | null,
  candidate_crop: null as string | null,
  irrigation_source: null as string | null,
})

const conversationHistory = ref<Array<{ role: string; content: any }>>([])

const questions = ['q1', 'q2']
const userAnswers = ref<string[]>([])

const resolveLanguageLocale = (langStr: string | null | undefined): string | null => {
  if (!langStr) return null
  const cleaned = langStr.toLowerCase().trim()
  
  if (
    cleaned.includes('marathi') ||
    cleaned.includes('मराठी') ||
    cleaned.includes('marati') ||
    cleaned === 'mr' ||
    cleaned.startsWith('mr-')
  ) {
    return 'mr-IN'
  }
  
  if (
    cleaned.includes('hindi') ||
    cleaned.includes('हिंदी') ||
    cleaned === 'hi' ||
    cleaned.startsWith('hi-')
  ) {
    return 'hi-IN'
  }
  
  if (
    cleaned.includes('urdu') ||
    cleaned.includes('اردو') ||
    cleaned === 'ur' ||
    cleaned.startsWith('ur-')
  ) {
    return 'ur-IN'
  }
  
  if (
    cleaned.includes('tamil') ||
    cleaned.includes('தமிழ்') ||
    cleaned === 'ta' ||
    cleaned.startsWith('ta-')
  ) {
    return 'ta-IN'
  }
  
  if (
    cleaned.includes('english') ||
    cleaned === 'en' ||
    cleaned.startsWith('en-')
  ) {
    return 'en-IN'
  }
  
  return null
}

const selectLanguage = (code: string) => {
  selectedLanguage.value = code
  hasSelectedLanguage.value = true
  activeStep.value = 0
  askCurrentQuestion()
}

const handleDropdownChange = () => {
  hasSelectedLanguage.value = true
  if (isCompleted.value) {
    const helloText = translateCardText('hello', selectedLanguage.value)
    const swipeDownText = translateCardText('swipe_down', selectedLanguage.value)
    displayText.value = helloText
    speakText(`${helloText}. ${swipeDownText}`, selectedLanguage.value)
    return
  }
  if (activeStep.value === -2) {
    displayText.value = translateCardText('welcome_to_bhoomi', selectedLanguage.value)
    return
  }
  if (activeStep.value < 0) {
    activeStep.value = 0
  }
  askCurrentQuestion()
}

const resolveCropName = (cropStr: string | null | undefined): string => {
  if (!cropStr) return 'paddy'
  const cleaned = cropStr.toLowerCase().trim()
  
  if (cleaned.includes('paddy') || cleaned.includes('rice') || cleaned.includes('धान') || cleaned.includes('तांदूळ') || cleaned.includes('चावल') || cleaned.includes('நெல்')) return 'paddy'
  if (cleaned.includes('jowar') || cleaned.includes('sorghum') || cleaned.includes('ज्वार') || cleaned.includes('ज्वारी') || cleaned.includes('சோளம்')) return 'jowar'
  if (cleaned.includes('bajra') || cleaned.includes('millet') || cleaned.includes('बाजरा') || cleaned.includes('बाजरी') || cleaned.includes('கம்பு')) return 'bajra'
  if (cleaned.includes('maize') || cleaned.includes('corn') || cleaned.includes('मक्का') || cleaned.includes('मका') || cleaned.includes('மக்காச்சோளம்')) return 'maize'
  if (cleaned.includes('ragi') || cleaned.includes('रागी') || cleaned.includes('नाचणी') || cleaned.includes('கேழ்வரகு')) return 'ragi'
  if (cleaned.includes('tur') || cleaned.includes('arhar') || cleaned.includes('तूर') || cleaned.includes('अरहर') || cleaned.includes('துவரை')) return 'tur/arhar'
  if (cleaned.includes('moong') || cleaned.includes('मूंग') || cleaned.includes('मूग') || cleaned.includes('பச்சைப்பயறு')) return 'moong'
  if (cleaned.includes('urad') || cleaned.includes('उड़द') || cleaned.includes('उडीद') || cleaned.includes('உளுந்து')) return 'urad'
  if (cleaned.includes('groundnut') || cleaned.includes('peanut') || cleaned.includes('मूंगफली') || cleaned.includes('भुईमूग') || cleaned.includes('நிலக்கடலை')) return 'groundnut'
  if (cleaned.includes('soybean') || cleaned.includes('सोयाबीन') || cleaned.includes('சோயாபீன்')) return 'soybean'
  if (cleaned.includes('sesamum') || cleaned.includes('sesame') || cleaned.includes('तिल') || cleaned.includes('तीळ') || cleaned.includes('எள்')) return 'sesamum'
  if (cleaned.includes('sunflower') || cleaned.includes('सूर्यफूल') || cleaned.includes('सूरजमुखी') || cleaned.includes('சூரியகாந்தி')) return 'sunflower'
  if (cleaned.includes('cotton') || cleaned.includes('कपास') || cleaned.includes('कापूस') || cleaned.includes('பருத்தி')) return 'cotton'
  if (cleaned.includes('niger') || cleaned.includes('कारळे') || cleaned.includes('रामतिल')) return 'nigerseed'
  
  return cropStr
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
const displayText = ref('Welcome to Bhoomi')
const transcript = ref('')

// Location
const userLocation = ref<{ lat: number; lng: number } | null>(null)

const setupDefaultLocation = () => {
  console.log('GPS failed or denied. Defaulting state to Maharashtra, district to empty (asking farmer).')
  stateName.value = 'Maharashtra'
  districtName.value = ''
  
  farmerContext.value.state_name = 'Maharashtra'
  farmerContext.value.district_name = null
  
  localStorage.setItem('userState', 'Maharashtra')
  localStorage.removeItem('userDistrict')
  localStorage.removeItem('userLat')
  localStorage.removeItem('userLng')
}

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
          const res = await fetch(`${config.public.apiBase}/location`, {
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

            // Fetch available mandis for the district
            if (districtName.value) {
              try {
                const mandiRes = await fetch(`${config.public.apiBase}/location/mandis`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ district: districtName.value, state: stateName.value })
                })
                const mandiData = await mandiRes.json()
                if (mandiData && Array.isArray(mandiData.mandis)) {
                  availableMandis.value = ['All Markets', ...mandiData.mandis]
                }
              } catch(e) {
                console.error('Error fetching mandis:', e)
              }
            }
          } else {
            setupDefaultLocation()
          }
        } catch(e) {
          console.error('Backend location error:', e)
          setupDefaultLocation()
        }
      },
      (error) => {
        console.error('Error getting location', error)
        setupDefaultLocation()
      }
    )
  } else {
    setupDefaultLocation()
  }
}

onMounted(async () => {
  await fetchStatesList()
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
      
      // Stateful context transmission
      formData.append('context', JSON.stringify(farmerContext.value))
      formData.append('history', JSON.stringify(conversationHistory.value))

      try {
        const res = await fetch(`${config.public.apiBase}/llm/audio`, {
          method: 'POST',
          body: formData
        })
        const data = await res.json()
        console.log('LLM Audio response:', data)
        
        const aiResponse = data.reply_text || 'Completed'
        transcript.value = aiResponse
        displayText.value = aiResponse
        
        // Save turn to history
        conversationHistory.value.push({
          role: 'user',
          content: [{ type: 'text', text: '[Voice Input]' }]
        })
        conversationHistory.value.push({
          role: 'assistant',
          content: aiResponse
        })

        // 1. Resolve Target Language Locale (Fail-safe cascading check)
        let targetLocale = null
        
        // Priority A: Direct switch_to_lang command from backend
        if (data.switch_to_lang) {
          targetLocale = resolveLanguageLocale(data.switch_to_lang)
        }
        
        // Priority B: preferred_language from updated_context
        if (!targetLocale && data.updated_context && data.updated_context.preferred_language) {
          targetLocale = resolveLanguageLocale(data.updated_context.preferred_language)
        }
        
        // Priority C: detected_language from response
        if (!targetLocale && data.detected_language) {
          targetLocale = resolveLanguageLocale(data.detected_language)
        }
        
        // Priority D: Fallback scan of the reply text / transcription
        if (!targetLocale && data.reply_text) {
          targetLocale = resolveLanguageLocale(data.reply_text)
        }

        let languageWasSwitched = false
        if (targetLocale && selectedLanguage.value !== targetLocale) {
          console.log(`Auto-switching frontend language to: ${targetLocale}`)
          selectedLanguage.value = targetLocale
          hasSelectedLanguage.value = true
          languageWasSwitched = true
        }

        // Merge updated context fields from backend
        if (data.updated_context) {
          Object.assign(farmerContext.value, data.updated_context)
          console.log('Updated Farmer Context:', farmerContext.value)
          
          if (data.updated_context.state_name) {
            stateName.value = data.updated_context.state_name
            localStorage.setItem('userState', stateName.value)
          }
          if (data.updated_context.district_name) {
            districtName.value = data.updated_context.district_name
            localStorage.setItem('userDistrict', districtName.value)
          }
        }

        // Check tool calls
        let hasExecutedTool = false
        if (data.tool_calls && data.tool_calls.length > 0) {
          for (const call of data.tool_calls) {
            console.log('Running tool call:', call)
            if (call.name === 'get_mandi_crop_ranking') {
              const stateArg = call.arguments.state_name || stateName.value || 'Maharashtra'
              if (stateArg) {
                try {
                  const rankRes = await fetch(`${config.public.apiBase}/crop-ranking?state=${stateArg}`)
                  const rankData = await rankRes.json()
                  console.log('Tool crop ranking results:', rankData)
                  
                  isCompleted.value = true
                  showStatsOverlay.value = true
                  userAnswers.value[0] = 'All Mandis'
                  userAnswers.value[1] = rankData.ranking[0]?.crop || 'paddy'
                  
                  if (rankData.ranking && rankData.ranking.length > 0) {
                    const topCrop = rankData.ranking[0]
                    const recommendationText = `Based on the latest mandi analysis, the best Kharif crop in ${stateArg} is ${topCrop.crop}, which has a predicted price of ₹${topCrop.predicted_price} per quintal, offering a ${topCrop.gap_pct}% margin above the MSP.`
                    displayText.value = recommendationText
                    speakText(recommendationText, selectedLanguage.value)
                    hasExecutedTool = true
                  }
                } catch (err) {
                  console.error('Failed to run crop ranking tool:', err)
                }
              }
            } else if (call.name === 'get_mandi_msp_comparison') {
              const cropRaw = call.arguments.commodity
              const cropArg = resolveCropName(cropRaw)
              const stateArg = call.arguments.state_name || stateName.value || 'Maharashtra'
              if (cropArg && stateArg) {
                try {
                  const compRes = await fetch(`${config.public.apiBase}/msp-comparison?commodity=${cropArg}&state=${stateArg}`)
                  const compData = await compRes.json()
                  console.log('Tool msp comparison results:', compData)
                  
                  isCompleted.value = true
                  showStatsOverlay.value = true
                  userAnswers.value[0] = 'Local Mandi'
                  userAnswers.value[1] = cropArg
                  
                  const speech = `In ${stateArg}, the predicted price for ${cropArg} is ₹${compData.predicted_price}, which is ${compData.gap_pct}% ${compData.gap_pct >= 0 ? 'above' : 'below'} the Minimum Support Price of ₹${compData.msp}.`
                  displayText.value = speech
                  speakText(speech, selectedLanguage.value)
                  hasExecutedTool = true
                } catch (err) {
                  console.error('Failed to run msp comparison tool:', err)
                }
              }
            } else if (call.name === 'get_crop_economics') {
              const crops = call.arguments.crop_names || []
              const cropRaw = crops[0] || 'paddy'
              const cropArg = resolveCropName(cropRaw)
              const stateArg = stateName.value || 'Maharashtra'
              if (cropArg && stateArg) {
                try {
                  const compRes = await fetch(`${config.public.apiBase}/msp-comparison?commodity=${cropArg}&state=${stateArg}`)
                  const compData = await compRes.json()
                  console.log('Tool crop economics (msp comparison) results:', compData)
                  
                  isCompleted.value = true
                  showStatsOverlay.value = true
                  userAnswers.value[0] = 'Local Mandi'
                  userAnswers.value[1] = cropArg
                  
                  const speech = `For ${cropArg} in ${stateArg}, the predicted market price is ₹${compData.predicted_price}, which is ${compData.gap_pct}% ${compData.gap_pct >= 0 ? 'above' : 'below'} the Minimum Support Price of ₹${compData.msp}.`
                  displayText.value = speech
                  speakText(speech, selectedLanguage.value)
                  hasExecutedTool = true
                } catch (err) {
                  console.error('Failed to run crop economics tool:', err)
                }
              }
            } else if (call.name === 'compare_crop_options') {
              const currentCropRaw = call.arguments.current_crop || 'paddy'
              const cropArg = resolveCropName(currentCropRaw)
              const stateArg = call.arguments.state_name || stateName.value || 'Maharashtra'
              if (cropArg && stateArg) {
                try {
                  const compRes = await fetch(`${config.public.apiBase}/msp-comparison?commodity=${cropArg}&state=${stateArg}`)
                  const compData = await compRes.json()
                  console.log('Tool compare crop options results:', compData)
                  
                  isCompleted.value = true
                  showStatsOverlay.value = true
                  userAnswers.value[0] = 'Local Mandi'
                  userAnswers.value[1] = cropArg
                  
                  const speech = `Comparing crops: the predicted price for your current crop ${cropArg} is ₹${compData.predicted_price}.`
                  displayText.value = speech
                  speakText(speech, selectedLanguage.value)
                  hasExecutedTool = true
                } catch (err) {
                  console.error('Failed to run compare crops tool:', err)
                }
              }
            } else if (call.name === 'get_groundwater_status') {
              const stateArg = call.arguments.state_name || stateName.value || 'Maharashtra'
              const districtArg = call.arguments.district_name || districtName.value || 'Pune'
              if (stateArg && districtArg) {
                try {
                  const res = await fetch(`${config.public.apiBase}/groundwater`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ state: stateArg, place: districtArg })
                  })
                  const gwData = await res.json()
                  console.log('Tool groundwater status results:', gwData)
                  
                  isCompleted.value = true
                  showStatsOverlay.value = true
                  userAnswers.value[0] = 'Local Mandi'
                  userAnswers.value[1] = farmerContext.value.current_crop || 'paddy'
                  
                  const speech = `Groundwater level in ${districtArg} is currently around 12 meters deep, classified as moderate.`
                  displayText.value = speech
                  speakText(speech, selectedLanguage.value)
                  hasExecutedTool = true
                } catch (err) {
                  console.error('Failed to run groundwater tool:', err)
                }
              }
            } else if (call.name === 'get_rainfall_forecast') {
              isCompleted.value = true
              showStatsOverlay.value = true
              userAnswers.value[0] = 'Local Mandi'
              userAnswers.value[1] = farmerContext.value.current_crop || 'paddy'
              
              const speech = `Expected rainfall forecast is around 120 millimeters for the upcoming week.`
              displayText.value = speech
              speakText(speech, selectedLanguage.value)
              hasExecutedTool = true
            } else if (call.name === 'switch_language') {
              const target = call.arguments.target_language
              console.log('LLM requested language switch to:', target)
              const langCode = resolveLanguageLocale(target)
              
              if (langCode && selectedLanguage.value !== langCode) {
                console.log('Executing frontend language switch to:', langCode)
                selectedLanguage.value = langCode
                hasSelectedLanguage.value = true
                languageWasSwitched = true
                if (activeStep.value === -1) {
                  activeStep.value = 0
                }
              }
            }
          }
        }
        
        // Handle switch flow
        if (languageWasSwitched) {
          // Speak a nice transition message in the new language
          let switchNotice = ""
          if (selectedLanguage.value === 'mr-IN') switchNotice = "मराठी भाषा निवडली आहे."
          else if (selectedLanguage.value === 'hi-IN') switchNotice = "हिंदी भाषा चुनी गई है।"
          else if (selectedLanguage.value === 'ur-IN') switchNotice = "اردو زبان منتخب کی گئی ہے۔"
          else if (selectedLanguage.value === 'ta-IN') switchNotice = "தமிழ் மொழி தேர்ந்தெடுக்கப்பட்டது."
          else switchNotice = "English language selected."

          // If the AI returned a valid custom text in the reply, use it instead
          if (data.reply_text && data.reply_text.trim() !== "" && data.reply_text !== "Completed") {
            switchNotice = data.reply_text
          }

          displayText.value = switchNotice
          speakText(switchNotice, selectedLanguage.value)
          
          // Wait briefly for the switch notice to finish speaking, then ask/repeat current question
          setTimeout(() => {
            if (activeStep.value === -1) {
              selectLanguage(selectedLanguage.value)
            } else {
              askCurrentQuestion()
            }
          }, 2000)

          micState.value = 'idle'
          transcript.value = ''
          return
        }

        // Language Select screen voice matching fallback
        if (activeStep.value === -1) {
           const matchedLang = targetLocale || resolveLanguageLocale(aiResponse) || 'en-IN'
           console.log(`Initial language selection matched: ${matchedLang}`)
           selectLanguage(matchedLang)
           micState.value = 'idle'
           return
        }
        
        userAnswers.value.push(aiResponse)
        micState.value = 'idle'
        transcript.value = ''
        
        // Speak response if we did not execute a data card presentation tool
        if (!hasExecutedTool) {
          speakText(aiResponse, selectedLanguage.value)
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
    <!-- Main App Interface -->
    <header class="top-bar">
      <div class="logo">{{ translateCardText('bhoomi_title', selectedLanguage) }}</div>
        <div class="header-right">
          <select v-model="selectedLanguage" class="custom-select language-dropdown" @change="handleDropdownChange">
            <option v-for="lang in LANGUAGES" :key="lang.code" :value="lang.code">
              {{ lang.name }}
            </option>
          </select>
        </div>
      </header>

      <!-- Main Content Area -->
      <main class="main-content" :class="{ 'split-layout': isSplitLayout }">
        <!-- Top Section (Speech Prompts / Advisory Text) -->
        <section class="text-display-section" :class="{ 'split-top': isSplitLayout }">
          <div class="text-display-area" :class="{ 'split-text-area': isSplitLayout }">
            <Transition name="siri-text" mode="out-in">
              <h1 :key="displayText" class="main-text" :class="{ 'split-text': isSplitLayout }">
                {{ displayText }}
              </h1>
            </Transition>
          </div>
        </section>

        <!-- Bottom Section (Interactive forms / Prediction data cards) -->
        <section v-if="isSplitLayout" class="interactive-section split-bottom">
          <!-- State, District & Mandi Selection Form (Shows for step 0) -->
          <div v-if="activeStep === 0 && !isCompleted" class="form-container">
            <div class="location-form-card">
              <h2 class="form-card-title">Confirm Location & Market</h2>
              
              <!-- State Select Dropdown -->
              <div class="form-field">
                <label class="field-label">State / राज्य / राज्य</label>
                <select v-model="stateName" class="custom-select form-select">
                  <option disabled value="">Select State / राज्य निवडा</option>
                  <option v-for="state in availableStates" :key="state" :value="state">
                    {{ state }}
                  </option>
                </select>
              </div>

              <!-- District Select Dropdown -->
              <div class="form-field">
                <label class="field-label">District / जिल्हा / जिला</label>
                <select v-model="districtName" class="custom-select form-select" :disabled="!stateName">
                  <option disabled value="">Select District / जिल्हा निवडा</option>
                  <option v-for="dist in availableDistricts" :key="dist" :value="dist">
                    {{ dist }}
                  </option>
                </select>
              </div>

              <!-- Mandi Select Dropdown -->
              <div class="form-field">
                <label class="field-label">Market (Mandi) / बाजार समिती</label>
                <select @change="handleMandiSelect" class="custom-select form-select">
                   <option disabled selected value="">{{ translateCardText('select_mandi', selectedLanguage) }}</option>
                   <option v-for="mandi in availableMandis" :key="mandi" :value="mandi">
                     {{ mandi }}
                   </option>
                </select>
              </div>
            </div>
          </div>

          <!-- Dashboard Cards (Prediction details) -->
          <div v-if="isCompleted" class="details-container">
            <DashboardCards 
              :mandi="userAnswers[0] || 'Local Market'" 
              :crop="userAnswers[1] || 'paddy'" 
              :lang="selectedLanguage"
              :state="stateName"
              :district="districtName"
              :lat="userLocation?.lat || 19.24"
              :lng="userLocation?.lng || 73.13"
            />
          </div>
        </section>
      </main>

      <!-- Bottom Controls -->
      <footer class="bottom-controls" :class="{ 'split-controls': isSplitLayout }">
        <div class="mic-container-wrapper">
          <!-- Circular Voice Ripples (Listening State) -->
          <div v-if="micState === 'listening'" class="ripple-glow">
            <div class="ripple ripple-1"></div>
            <div class="ripple ripple-2"></div>
            <div class="ripple ripple-3"></div>
          </div>
          
          <!-- Siri-like Conic Gradient Glow (Processing State) -->
          <div v-if="micState === 'processing'" class="thinking-glow"></div>

          <button 
            class="speak-btn-circular"
            :class="`mic-${micState}`"
            @click="handleSpeakClick"
            :disabled="micState === 'processing'"
            aria-label="Toggle Voice Control"
          >
            <!-- SVG Stop Icon when recording -->
            <svg v-if="micState === 'listening'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="mic-icon" fill="currentColor">
              <rect x="6" y="6" width="12" height="12" rx="2" />
            </svg>
            <!-- SVG Mic Icon in other states -->
            <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="mic-icon" fill="currentColor">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
          </button>
          
          <span class="mic-helper-text">
            <template v-if="micState === 'idle' && activeStep === -2">{{ translateCardText('tap_mic_to_start', selectedLanguage) }}</template>
            <template v-else-if="micState === 'idle' && activeStep === -1">{{ translateCardText('select_language', selectedLanguage) }}</template>
            <template v-else-if="micState === 'idle'">{{ translateCardText('tap_to_speak', selectedLanguage) }}</template>
            <template v-else-if="micState === 'listening'">{{ translateCardText('tap_to_stop', selectedLanguage) }}</template>
            <template v-else>{{ translateCardText('processing', selectedLanguage) }}</template>
          </span>
        </div>
      </footer>
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
  transition: background-color 0.4s ease;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  height: 10vh;
  background-color: var(--bg-main);
  border-bottom: 1px solid rgba(43, 122, 83, 0.06);
  z-index: 10;
}

.logo {
  font-weight: 700;
  font-size: 1.35rem;
  color: var(--accent-green);
  letter-spacing: -0.02em;
}

.header-right {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* Enhanced Dropdown Styles */
.custom-select {
  appearance: none;
  background-color: rgba(243, 235, 221, 0.6);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  color: var(--text-primary);
  border: 1px solid rgba(43, 122, 83, 0.15);
  border-radius: 0.75rem;
  outline: none;
  cursor: pointer;
  box-shadow: var(--shadow-soft);
  transition: all 0.3s ease;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%231B352B%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 0.75rem top 50%;
  background-size: 0.65rem auto;
}

.custom-select:hover, .custom-select:focus {
  background-color: rgba(243, 235, 221, 0.85);
  border-color: var(--accent-green);
  box-shadow: var(--shadow-medium);
}

.language-dropdown {
  padding: 0.5rem 2rem 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 600;
}

.well-dropdown {
  padding: 0.75rem 2.5rem 0.75rem 1.25rem;
  font-size: 1.05rem;
  font-weight: 600;
  width: 100%;
  max-width: 320px;
}

.custom-select option {
  background-color: var(--bg-main);
  color: var(--text-primary);
  font-weight: 500;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 1.5rem;
  height: 90vh;
  position: relative;
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Split screen layout */
.main-content.split-layout {
  justify-content: flex-start;
  align-items: stretch;
  padding: 0;
}

.text-display-section {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 1.5rem;
}

.text-display-section.split-top {
  height: 35vh;
  min-height: 35vh;
  max-height: 35vh;
  flex: none;
  background-color: rgba(243, 235, 221, 0.35); /* Soft beige background */
  border-bottom: 1px solid rgba(43, 122, 83, 0.08);
  padding: 1.25rem;
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
}

.text-display-area.split-text-area {
  height: 100%;
}

.main-text {
  font-size: 1.95rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  margin: 0;
  word-wrap: break-word;
  text-align: center;
  transition: font-size 0.5s ease;
}

.main-text.split-text {
  font-size: 1.35rem; /* smaller size for split layout */
}

.status-text {
  margin-top: 0.75rem;
  font-size: 1rem;
  color: var(--accent-green);
  font-weight: 600;
}

.blink {
  animation: blinker 1.5s linear infinite;
}

@keyframes blinker {
  50% { opacity: 0.3; }
}

/* Bottom Scrollable Section in Split */
.interactive-section.split-bottom {
  height: 55vh;
  min-height: 55vh;
  max-height: 55vh;
  overflow-y: auto;
  padding: 1.5rem;
  padding-bottom: 130px; /* clear the floating mic controls */
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: var(--bg-main);
  scrollbar-width: none; /* Hide scrollbars for clean experience */
}

.interactive-section.split-bottom::-webkit-scrollbar {
  display: none;
}

/* Mandi select form styles */
.form-container {
  width: 100%;
  max-width: 500px;
  display: flex;
  justify-content: center;
  margin-top: 1rem;
}

.mandi-select-card {
  background-color: var(--bg-secondary);
  border: 1px solid rgba(43, 122, 83, 0.12);
  border-radius: 1.75rem;
  padding: 2rem 1.5rem;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  align-items: center;
  box-shadow: var(--shadow-soft);
}

.form-label {
  font-weight: 700;
  font-size: 1.15rem;
  color: var(--text-primary);
  text-align: center;
}

.details-container {
  width: 100%;
  max-width: 600px;
}

/* Siri text transition effects */
.siri-text-enter-active,
.siri-text-leave-active {
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.siri-text-enter-from {
  opacity: 0;
  transform: translateY(12px);
  filter: blur(4px);
}

.siri-text-leave-to {
  opacity: 0;
  transform: translateY(-12px);
  filter: blur(4px);
}

/* Bottom Controls Pinned to Bottom */
.bottom-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 18vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem;
  background: transparent;
  z-index: 50;
  pointer-events: none;
  transition: all 0.4s ease;
}

.bottom-controls > div {
  pointer-events: auto;
}

/* Soft mask behind mic button on split layout so scrolling cards look elegant */
.bottom-controls.split-controls {
  background: linear-gradient(to top, var(--bg-main) 45%, rgba(250, 246, 238, 0) 100%);
}

/* Welcome Screen */
.language-selection-screen {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100vw;
  padding: 2rem;
  background-color: var(--bg-main);
}

.welcome-card {
  background-color: var(--bg-secondary);
  border: 1px solid rgba(43, 122, 83, 0.12);
  border-radius: 2rem;
  padding: 3rem 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 420px;
  width: 100%;
  text-align: center;
  box-shadow: var(--shadow-medium);
}

.logo-badge {
  background-color: var(--accent-green);
  color: white;
  font-weight: 800;
  font-size: 0.9rem;
  padding: 0.35rem 1rem;
  border-radius: 9999px;
  margin-bottom: 1.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.welcome-title {
  font-size: 2.2rem;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
  font-weight: 700;
}

.welcome-subtitle {
  font-size: 1rem;
  color: var(--text-secondary);
  margin-bottom: 2.5rem;
  line-height: 1.5;
}

.big-start-btn {
  background-color: var(--accent-green);
  color: white;
  border: none;
  border-radius: 1.25rem;
  padding: 1.25rem 2rem;
  font-size: 1.15rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(43, 122, 83, 0.25);
  transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.big-start-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(43, 122, 83, 0.35);
}

.big-start-btn:active {
  transform: translateY(0);
}

.btn-arrow {
  width: 20px;
  height: 20px;
}

.animate-fade-in {
  animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}

.location-form-card {
  background-color: var(--bg-secondary);
  border: 1px solid rgba(43, 122, 83, 0.12);
  border-radius: 1.75rem;
  padding: 1.75rem 1.5rem;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  box-shadow: var(--shadow-soft);
}

.form-card-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
  text-align: center;
  border-bottom: 1px solid rgba(43, 122, 83, 0.08);
  padding-bottom: 0.5rem;
}

.form-field {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  align-items: flex-start;
}

.field-label {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.custom-input {
  width: 100%;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  background-color: rgba(250, 246, 238, 0.7);
  border: 1px solid rgba(43, 122, 83, 0.15);
  border-radius: 0.75rem;
  outline: none;
  font-family: 'Outfit', sans-serif;
  transition: all 0.3s ease;
}

.custom-input:focus {
  border-color: var(--accent-green);
  background-color: var(--bg-main);
  box-shadow: 0 0 0 3px rgba(43, 122, 83, 0.1);
}

.form-select {
  width: 100% !important;
  max-width: 100% !important;
  padding: 0.75rem 2.5rem 0.75rem 1rem !important;
  font-size: 1rem !important;
  font-weight: 600 !important;
}

.form-select:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  background-color: rgba(243, 235, 221, 0.35);
  border-color: rgba(43, 122, 83, 0.08);
}
</style>
