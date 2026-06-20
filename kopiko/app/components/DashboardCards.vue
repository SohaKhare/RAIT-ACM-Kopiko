<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { translateCardText } from '../utils/gemini'

const props = defineProps({
  crop: {
    type: String,
    default: 'paddy'
  },
  mandi: {
    type: String,
    default: 'Local Market'
  },
  lang: {
    type: String,
    required: true
  },
  state: {
    type: String,
    default: 'Maharashtra'
  },
  district: {
    type: String,
    default: 'Pune'
  },
  lat: {
    type: Number,
    default: 19.24
  },
  lng: {
    type: Number,
    default: 73.13
  }
})

// Component Logic

const config = useRuntimeConfig()
const groundwaterLevel = ref(12)
const groundwaterPercentage = ref(60)
const rainfall = ref('120mm')
const priceTrend = ref('+0.0%')
const price = ref('₹0 / quintal')
const mspPrice = ref('₹0 / quintal')
const loading = ref(true)

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
  if (cleaned.includes('cotton') || cleaned.includes('कपास') || cleaned.includes('कापूस') || cleaned.includes('பруத்தி')) return 'cotton'
  if (cleaned.includes('niger') || cleaned.includes('कारळे') || cleaned.includes('रामतिल')) return 'nigerseed'
  
  return cropStr
}

const fetchData = async () => {
  loading.value = true
  try {
    // 1. Fetch Mandi price comparison
    const resolvedCrop = resolveCropName(props.crop)
    const stateVal = props.state || 'Maharashtra'
    const mspRes = await fetch(`${config.public.apiBase}/msp-comparison?commodity=${resolvedCrop}&state=${stateVal}`)
    const mspData = await mspRes.json()
    if (mspData && !mspData.detail) {
      price.value = `₹${Math.round(mspData.predicted_price).toLocaleString()} / quintal`
      mspPrice.value = `₹${Math.round(mspData.msp).toLocaleString()} / quintal`
      priceTrend.value = `${mspData.gap_pct >= 0 ? '↑' : '↓'} ${Math.abs(mspData.gap_pct).toFixed(1)}% ${mspData.gap_pct >= 0 ? 'above' : 'below'} MSP`
    }
  } catch (err) {
    console.error('Error fetching crop economics in DashboardCards:', err)
  }

  try {
    // 2. Fetch Groundwater Status
    const gwRes = await fetch(`${config.public.apiBase}/groundwater`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state: props.state || 'Maharashtra', place: props.district || 'Pune' })
    })
    const gwData = await gwRes.json()
    if (gwData && gwData.current_depth) {
      groundwaterLevel.value = gwData.current_depth
      groundwaterPercentage.value = Math.min(100, Math.max(0, (gwData.current_depth / 40) * 100))
    }
  } catch (err) {
    console.error('Error fetching groundwater status in DashboardCards:', err)
  }

  try {
    // 3. Fetch Weather Data
    const weatherRes = await fetch(`${config.public.apiBase}/weather`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat: props.lat, lng: props.lng })
    })
    const weatherData = await weatherRes.json()
    if (weatherData && weatherData.forecast_7_total_mm !== undefined) {
      rainfall.value = `${Math.round(weatherData.forecast_7_total_mm)}mm`
    }
  } catch (err) {
    console.error('Error fetching weather data in DashboardCards:', err)
  }
  loading.value = false
}

onMounted(() => {
  fetchData()
})

watch(() => [props.crop, props.state, props.district, props.lat, props.lng], () => {
  fetchData()
})
</script>

<template>
  <div class="dashboard-container">
    <h2 class="dashboard-title">{{ translateCardText('advisory_dashboard', props.lang) }}</h2>
    
    <!-- Loading indicator -->
    <div v-if="loading" class="info-card" style="align-items: center; justify-content: center; padding: 2rem;">
      <span class="card-title">Loading Advisory Data...</span>
    </div>

    <template v-else>
      <!-- Groundwater Card -->
      <div class="info-card">
        <div class="card-header">
          <span class="card-title">{{ translateCardText('groundwater_level', props.lang) }}</span>
          <span class="card-value">{{ groundwaterLevel }}m {{ translateCardText('depth', props.lang) }}</span>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar-fill" :style="{ width: groundwaterPercentage + '%' }"></div>
        </div>
        <div class="progress-labels">
          <span>0m</span>
          <span>40m</span>
        </div>
      </div>

      <!-- Rainfall Card -->
      <div class="info-card">
        <div class="card-header">
          <span class="card-title">{{ translateCardText('expected_rainfall', props.lang) }}</span>
          <span class="card-value">{{ rainfall }}</span>
        </div>
      </div>

      <!-- Mandi Prices Card -->
      <div class="info-card">
        <div class="card-header">
          <span class="card-title">🌾 {{ props.crop }} {{ translateCardText('price', props.lang) }} ({{ props.mandi }})</span>
          <div class="price-info">
            <span class="price">{{ price }}</span>
            <span class="trend" :style="{ color: priceTrend.includes('↓') ? '#FAF6EE' : '#FAF6EE' }">{{ priceTrend }}</span>
          </div>
        </div>
        <div class="card-header" style="margin-top: 0.5rem; font-size: 0.9rem; opacity: 0.85; border-top: 1px solid rgba(250, 246, 238, 0.15); padding-top: 0.5rem;">
          <span>Government MSP:</span>
          <span>{{ mspPrice }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard-container {
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.dashboard-title {
  color: var(--text-primary);
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  text-align: center;
  letter-spacing: -0.01em;
}

/* Card Layout: Full scale, horizontal pill shaped, border rounded-2xl, sea green #2E8B57, beige text */
.info-card {
  width: 100%;
  background-color: var(--card-bg, #2B7A53);
  color: var(--text-card, #FAF6EE);
  border-radius: 1.5rem; /* rounded-2xl */
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  box-shadow: 0 8px 24px rgba(43, 122, 83, 0.15);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.info-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(43, 122, 83, 0.22);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.card-title {
  font-weight: 600;
  font-size: 1.05rem;
  letter-spacing: -0.01em;
}

.card-value {
  font-weight: 700;
  font-size: 1.05rem;
}

/* Groundwater Progress Bar */
.progress-bar-container {
  width: 100%;
  height: 10px;
  background-color: rgba(250, 246, 238, 0.25); /* Transparent beige */
  border-radius: 10px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background-color: var(--text-card, #FAF6EE);
  border-radius: 10px;
  transition: width 1s ease-in-out;
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  opacity: 0.75;
  font-weight: 500;
}

.price-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.price {
  font-weight: 700;
  font-size: 1.2rem;
}

.trend {
  font-size: 0.8rem;
  color: var(--accent-green);
  background-color: var(--text-card); /* cream background pill on green card */
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  font-weight: 700;
  margin-top: 0.35rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
</style>
