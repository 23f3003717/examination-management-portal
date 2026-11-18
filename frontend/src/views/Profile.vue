<template>
  <div class="mx-auto" style="max-width: 760px">
    <div class="eyebrow">MY ACCOUNT</div><h1 class="page-title">Edit profile</h1><p class="text-secondary">Update your student contact details.</p>
    <div v-if="error" class="alert alert-danger">{{ error }}</div><div v-if="success" class="alert alert-success">{{ success }}</div>
    <form class="card panel-card" @submit.prevent="save"><div class="card-body p-4">
      <div class="mb-3"><label class="form-label" for="name">Full name</label><input id="name" v-model.trim="form.name" class="form-control" required maxlength="120"></div>
      <div class="mb-3"><label class="form-label" for="email">Email address</label><input id="email" :value="form.email" class="form-control" disabled><div class="form-text">Email changes are disabled here to preserve account identity.</div></div>
      <div class="mb-3"><label class="form-label" for="department">Department</label><input id="department" v-model.trim="form.department" class="form-control" maxlength="120"></div>
      <div class="mb-4"><label class="form-label" for="contact">Contact details</label><textarea id="contact" v-model.trim="form.contact_details" class="form-control" rows="3" maxlength="500" placeholder="Phone number or other contact information"></textarea></div>
      <button class="btn btn-primary" type="submit" :disabled="saving">{{ saving ? 'Saving…' : 'Save profile' }}</button> <router-link class="btn btn-outline-secondary ms-2" to="/">Back to dashboard</router-link>
    </div></form>
  </div>
</template>
<script>
import { api } from '../services/api'
export default {
  data: () => ({ form: { name: '', email: '', department: '', contact_details: '' }, saving: false, error: '', success: '' }),
  async mounted() { try { const r = await api.get('/auth/profile'); this.form = { ...this.form, ...r.data.user } } catch (e) { this.error = e.response?.data?.error || 'Could not load profile' } },
  methods: { async save() { this.saving = true; this.error = ''; this.success = ''; try { const r = await api.put('/auth/profile', { name: this.form.name, department: this.form.department, contact_details: this.form.contact_details }); this.form = { ...this.form, ...r.data.user }; this.success = 'Profile updated successfully.' } catch (e) { this.error = e.response?.data?.error || 'Could not update profile' } finally { this.saving = false } } }
}
</script>
