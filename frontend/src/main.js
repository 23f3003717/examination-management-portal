import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'
import './assets/styles.css'
import App from './App.vue'
import Login from './views/Login.vue'
import Dashboard from './views/Dashboard.vue'
import Examinations from './views/Examinations.vue'
import Bookings from './views/Bookings.vue'
import AdminManage from './views/AdminManage.vue'
import AdminUsers from './views/AdminUsers.vue'
import Profile from './views/Profile.vue'
import { api } from './services/api'

const routes = [
 {path:'/login',component:Login},
 {path:'/',component:Dashboard,meta:{auth:true}},
 {path:'/examinations',component:Examinations,meta:{auth:true}},
 {path:'/bookings',component:Bookings,meta:{auth:true}},
 {path:'/profile',component:Profile,meta:{auth:true,roles:['student']}},
 {path:'/admin',component:AdminManage,meta:{auth:true,roles:['admin']}},
 {path:'/admin/users',component:AdminUsers,meta:{auth:true,roles:['admin']}},
 {path:'/:pathMatch(.*)*',redirect:'/'}
]
const router=createRouter({history:createWebHistory(),routes})
router.beforeEach(async to=>{
 if(!to.meta.auth)return true
 try{
  const r=await api.get('/auth/me')
  if(to.meta.roles && !to.meta.roles.includes(r.data.user.role))return '/'
  return true
 }catch{return '/login'}
})
createApp(App).use(router).mount('#app')
