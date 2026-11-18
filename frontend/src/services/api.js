import axios from 'axios'

// Keep the host consistent with the frontend origin (localhost:8081) so
// the browser can send the session cookie reliably during local development.
export const api = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:5000/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' }
})
