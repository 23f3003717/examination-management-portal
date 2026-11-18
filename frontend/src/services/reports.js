import {api} from './api'; export const getAdminDashboard=()=>api.get('/admin/dashboard'); export const getReports=()=>api.get('/reports/summary')
