<template>
  <div class="admin-users-page">
    <div class="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
      <div>
        <div class="eyebrow">ADMIN</div>
        <h1 class="page-title">Saved users</h1>
        <p class="text-secondary mb-0">Users currently stored in the SQLite database.</p>
      </div>
      <button class="btn btn-outline-primary" @click="loadUsers" :disabled="loading">
        {{ loading ? 'Refreshing…' : 'Refresh' }}
      </button>
    </div>

    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

    <div class="card panel-card">
      <div class="card-header bg-white d-flex justify-content-between align-items-center">
        <h2 class="h5 mb-0">Users</h2>
        <span class="badge text-bg-light">{{ users.length }} total</span>
      </div>

      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Department</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>#{{ user.id }}</td>
              <td>{{ user.name || '—' }}</td>
              <td>{{ user.email || '—' }}</td>
              <td><span class="badge text-bg-light">{{ user.role || '—' }}</span></td>
              <td>{{ user.department || '—' }}</td>
              <td>
                <span
                  class="badge"
                  :class="user.account_status === 'active' ? 'text-bg-success' : 'text-bg-secondary'"
                >
                  {{ user.account_status || '—' }}
                </span>
              </td>
              <td>{{ user.created_at || '—' }}</td>
            </tr>
            <tr v-if="!users.length">
              <td colspan="7" class="text-center text-secondary py-4">
                No users have been saved to the database yet.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '../services/api'

export default {
  data() {
    return {
      users: [],
      loading: false,
      error: ''
    }
  },
  mounted() {
    this.loadUsers()
  },
  methods: {
    async loadUsers() {
      this.loading = true
      this.error = ''

      try {
        const response = await api.get('/admin/users')
        this.users = response.data.items || []
      } catch (e) {
        this.error = e.response?.data?.error || 'Unable to load saved users.'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.admin-users-page {
  max-width: 1100px;
  margin: 0 auto;
}

.panel-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.table th {
  font-size: 0.76rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #64748b;
  white-space: nowrap;
}

.table td {
  font-size: 0.92rem;
}
</style>
