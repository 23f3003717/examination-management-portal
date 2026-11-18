<template>
  <div class="app-shell">
    <nav
  v-if="!['/login', '/signup'].includes($route.path)"
  class="navbar navbar-expand-lg navbar-dark topbar"
>
      <div class="container-fluid"><router-link class="navbar-brand fw-bold" to="/">EMP <span class="brand-light">/ Examination Portal</span></router-link>
        <button class="navbar-toggler" data-bs-toggle="collapse" data-bs-target="#nav"><span class="navbar-toggler-icon"></span></button>
        <div id="nav" class="collapse navbar-collapse"><div class="navbar-nav ms-auto">
          <router-link class="nav-link" to="/">Dashboard</router-link><router-link class="nav-link" to="/examinations">Examinations</router-link><router-link class="nav-link" to="/bookings">Bookings</router-link><router-link v-if="role==='student'" class="nav-link" to="/profile">My Profile</router-link>
          <router-link v-if="role==='admin'" class="nav-link" to="/admin">Administration</router-link>
          <router-link v-if="role==='admin'" class="nav-link" to="/admin/users">Users</router-link>
          <button v-if="user" class="btn btn-sm btn-outline-light ms-lg-3" @click="logout">Sign out</button>
          <router-link v-else class="btn btn-sm btn-light ms-lg-3" to="/login">Sign in</router-link>
        </div></div>
      </div>
    </nav>
    <main class="container-fluid px-3 px-lg-5 py-4"><router-view @auth-changed="loadUser"/></main>
    <footer class="footer text-center py-3">Examination Management Portal · Local academic project</footer>
  </div>
</template>
<script>
import {api} from './services/api'
export default {data:()=>({user:null}),computed:{role(){return this.user?.role}},async mounted(){await this.loadUser()},methods:{
 async loadUser(){try{this.user=(await api.get('/auth/me')).data.user}catch{this.user=null}},
 async logout(){try{await api.post('/auth/logout')}finally{this.user=null;this.$router.push('/login')}}
}}
</script>
