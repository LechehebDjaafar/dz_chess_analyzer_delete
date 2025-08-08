import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

// إعداد Axios للـ API
const API_BASE = 'http://localhost:8000/api'
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  }
})

export const usePlayersStore = defineStore('players', () => {
  // الحالة
  const players = ref([])
  const currentPlayer = ref(null)
  const leaderboard = ref({ by_rating: [], by_wins: [] })
  const loading = ref(false)
  const error = ref(null)

  // Computed
  const playersCount = computed(() => players.value.length)
  const topPlayers = computed(() => 
    leaderboard.value.by_rating.slice(0, 5)
  )

  // Actions
  async function fetchPlayers() {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get('/players/')
      if (response.data.success) {
        players.value = response.data.players
      } else {
        throw new Error('فشل في جلب اللاعبين')
      }
    } catch (err) {
      error.value = err.response?.data?.error || err.message
      console.error('خطأ في جلب اللاعبين:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchPlayerDetails(username) {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get(`/players/${username}/`)
      if (response.data.success) {
        currentPlayer.value = response.data
        return response.data
      } else {
        throw new Error('فشل في جلب تفاصيل اللاعب')
      }
    } catch (err) {
      error.value = err.response?.data?.error || err.message
      console.error('خطأ في جلب تفاصيل اللاعب:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function addPlayer(playerData) {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.post('/players/add/', playerData)
      if (response.data.success) {
        // إضافة اللاعب للقائمة المحلية
        players.value.push(response.data.player)
        return response.data
      } else {
        throw new Error(response.data.error || 'فشل في إضافة اللاعب')
      }
    } catch (err) {
      error.value = err.response?.data?.error || err.message
      console.error('خطأ في إضافة اللاعب:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchLeaderboard() {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get('/players/leaderboard/')
      if (response.data.success) {
        leaderboard.value = response.data.leaderboards
      } else {
        throw new Error('فشل في جلب لوحة الصدارة')
      }
    } catch (err) {
      error.value = err.response?.data?.error || err.message
      console.error('خطأ في جلب لوحة الصدارة:', err)
    } finally {
      loading.value = false
    }
  }

  async function analyzePlayer(username) {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.post('/players/analyze/', { username })
      if (response.data.success) {
        return response.data
      } else {
        throw new Error(response.data.error || 'فشل في تحليل اللاعب')
      }
    } catch (err) {
      error.value = err.response?.data?.error || err.message
      console.error('خطأ في تحليل اللاعب:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  // إعادة تعيين الحالة
  function clearError() {
    error.value = null
  }

  function clearCurrentPlayer() {
    currentPlayer.value = null
  }

  return {
    // State
    players,
    currentPlayer,
    leaderboard,
    loading,
    error,
    
    // Getters
    playersCount,
    topPlayers,
    
    // Actions
    fetchPlayers,
    fetchPlayerDetails,
    addPlayer,
    fetchLeaderboard,
    analyzePlayer,
    clearError,
    clearCurrentPlayer
  }
})
