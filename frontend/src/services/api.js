import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Patients
  getPatients: () => api.get('/patients/'),
  getPatient: (id) => api.get(`/patients/${id}/`),

  // Health/Santé
  getHealthData: () => api.get('/sante/'),
  
  // Nutrition
  getNutrition: () => api.get('/nutrition/'),

  // Physical Activity
  getActivities: () => api.get('/activite-physique/'),

  // Gym Sessions
  getGymSessions: () => api.get('/gym-sessions/'),

  // KPIs
  getKPIs: () => api.get('/kpis/'),
  getEngagementKPIs: () => api.get('/engagement/'),
  getConversionKPIs: () => api.get('/conversion/'),
  getSatisfactionKPIs: () => api.get('/satisfaction/'),
  getDataQualityKPIs: () => api.get('/data-quality/'),
};

export default api;