<script setup lang="ts">
import { ref } from 'vue'
import { translateCardText } from '../utils/gemini'

const props = defineProps({
  crop: {
    type: String,
    default: 'Wheat'
  },
  mandi: {
    type: String,
    default: 'Local Market'
  },
  lang: {
    type: String,
    required: true
  }
})

// Dummy data for infographics
const groundwaterLevel = 12 // out of 20 meters
const groundwaterPercentage = (groundwaterLevel / 20) * 100

const rainfall = '120mm'
const priceTrend = '+5.2%'
const price = '₹2,400 / quintal'
</script>

<template>
  <div class="dashboard-container">
    <h2 class="dashboard-title">{{ translateCardText('advisory_dashboard', props.lang) }}</h2>
    
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
        <span>20m</span>
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
          <span class="trend">{{ priceTrend }}</span>
        </div>
      </div>
    </div>
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
  color: var(--text-beige);
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  text-align: center;
}

/* Card Layout: Full scale, horizontal pill shaped, border rounded-2xl, sea green #2E8B57, beige text */
.info-card {
  width: 100%;
  background-color: var(--card-bg, #2E8B57);
  color: var(--text-card, #F4EFE6);
  border-radius: 2rem; /* rounded-2xl */
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.card-title {
  font-weight: 600;
  font-size: 1.1rem;
}

.card-value {
  font-weight: 500;
  font-size: 1.1rem;
}

/* Groundwater Progress Bar */
.progress-bar-container {
  width: 100%;
  height: 12px;
  background-color: rgba(244, 239, 230, 0.3); /* Transparent beige */
  border-radius: 10px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background-color: var(--text-card, #F4EFE6);
  border-radius: 10px;
  transition: width 1s ease-in-out;
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  opacity: 0.8;
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
  font-size: 0.9rem;
  color: #a7f3d0; /* light green for positive trend */
}
</style>
