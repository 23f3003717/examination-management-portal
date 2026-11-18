import {api} from './api'; export const authService={me:()=>api.get('/auth/me'),login:data=>api.post('/auth/login',data),logout:()=>api.post('/auth/logout')}
