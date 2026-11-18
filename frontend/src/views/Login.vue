
<template>
  <div class="auth-page">
    <div class="auth-card">

      <!-- Header -->
      <div class="auth-header">
        <div class="logo-icon">🎓</div>
        <h1>Examination Portal</h1>
        <p>
          {{ showRegister
            ? 'Create your student account'
            : 'Login to your account' }}
        </p>
      </div>

      <div class="auth-body">
        <!-- Messages -->
        <div v-if="error" class="message error-message">
          {{ error }}
        </div>

        <div v-if="success" class="message success-message">
          {{ success }}
        </div>

        <!-- LOGIN FORM -->
        <form v-if="!showRegister" @submit.prevent="login">
          <h2>Welcome Back!</h2>
          <p class="subtitle">Please log in to continue.</p>

          <div class="form-group">
            <label>Email Address</label>
            <input
              v-model.trim="email"
              type="email"
              placeholder="Enter your email"
              autocomplete="username"
              required
            />
          </div>

          <div class="form-group">
            <label>Password</label>
            <input
              v-model="password"
              type="password"
              placeholder="Enter your password"
              autocomplete="current-password"
              required
            />
          </div>

          <button
            class="primary-button"
            type="submit"
            :disabled="loading"
          >
            {{ loading ? 'Signing in...' : 'Login' }}
          </button>

          <div class="separator"><span>OR</span></div>

          <p class="switch-text">
            New student?
            <button
              type="button"
              class="text-button"
              @click="openRegister"
            >
              Sign up
            </button>
          </p>

          <!-- <div class="info-box">
            <strong>ⓘ Login Information</strong>
            <ul>
              <li>Students, Examiners and Admins can log in.</li>
              <li>Only students can self-register.</li>
              <li>Admin and Examiner accounts are created by
                the system or Admin.</li>
            </ul>
          </div> -->
        </form>

        <!-- STUDENT REGISTRATION FORM -->
        <form v-else @submit.prevent="register">
          <h2>Create Account</h2>
          <p class="subtitle">
            Register as a student to access the portal.
          </p>

          <div class="form-group">
            <label>Full Name</label>
            <input
              v-model.trim="name"
              type="text"
              placeholder="Enter your full name"
              autocomplete="name"
              required
            />
          </div>

          <div class="form-group">
            <label>Email Address</label>
            <input
              v-model.trim="regEmail"
              type="email"
              placeholder="Enter your email address"
              autocomplete="email"
              required
            />
          </div>

          <div class="form-group">
            <label>Password</label>
            <input
              v-model="regPassword"
              type="password"
              placeholder="Create a password (8+ characters)"
              autocomplete="new-password"
              minlength="8"
              required
            />
          </div>

          <div class="form-group">
            <label>Confirm Password</label>
            <input
              v-model="confirmPassword"
              type="password"
              placeholder="Confirm your password"
              autocomplete="new-password"
              minlength="8"
              required
            />
          </div>

          <button
            class="primary-button"
            type="submit"
            :disabled="loading"
          >
            {{ loading ? 'Creating account...' : 'Create student account' }}
          </button>

          <p class="switch-text">
            Already have an account?
            <button
              type="button"
              class="text-button"
              @click="openLogin"
            >
              Login
            </button>
          </p>
        </form>
      </div>

      <div class="auth-footer">
        Examination Management Portal
      </div>
    </div>
  </div>
</template>

<script>
import { api } from '../services/api'

export default {
  data() {
    return {
      showRegister: false,
      email: '',
      password: '',
      name: '',
      regEmail: '',
      regPassword: '',
      confirmPassword: '',
      error: '',
      success: '',
      loading: false
    }
  },

  methods: {
    openRegister() {
      this.showRegister = true
      this.error = ''
      this.success = ''
    },

    openLogin() {
      this.showRegister = false
      this.error = ''
      this.success = ''
    },

    async login() {
      this.error = ''
      this.success = ''
      this.loading = true

      try {
        const response = await api.post('/auth/login', {
          email: this.email,
          password: this.password
        })

        const role = response.data?.user?.role

        if (!['student', 'admin', 'examiner'].includes(role)) {
          this.error = 'This account has an unsupported role.'
          return
        }

        this.$emit('auth-changed')
        await this.$router.push('/')
      } catch (e) {
        this.error =
          e.response?.data?.error ||
          'Could not sign in. Check your email and password.'
      } finally {
        this.loading = false
      }
    },

    async register() {
      this.error = ''
      this.success = ''

      if (this.regPassword !== this.confirmPassword) {
        this.error = 'Passwords do not match.'
        return
      }

      if (this.regPassword.length < 8) {
        this.error = 'Password must be at least 8 characters.'
        return
      }

      this.loading = true

      try {
        await api.post('/auth/register', {
          name: this.name,
          email: this.regEmail,
          password: this.regPassword
        })

        this.email = this.regEmail
        this.password = this.regPassword
        this.showRegister = false
        this.success = 'Account created successfully. Please log in.'
        this.name = ''
        this.regEmail = ''
        this.regPassword = ''
        this.confirmPassword = ''
      } catch (e) {
        this.error =
          e.response?.data?.error ||
          'Registration failed. Please try again.'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 35px 16px;
  background: #eff6ff;
  font-family: Arial, sans-serif;
}

.auth-card {
  width: 100%;
  max-width: 470px;
  background: #ffffff;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 8px 28px rgba(30, 64, 110, 0.12);
}

.auth-header {
  background: #244a7c;
  color: white;
  text-align: center;
  padding: 28px 20px 24px;
}

.logo-icon {
  font-size: 38px;
  margin-bottom: 8px;
}

.auth-header h1 {
  font-size: 25px;
  font-weight: 700;
  margin: 0 0 8px;
}

.auth-header p {
  color: #dbeafe;
  margin: 0;
  font-size: 14px;
}

.auth-body {
  padding: 28px;
}

.auth-body h2 {
  font-size: 23px;
  color: #1e3557;
  font-weight: 700;
  margin: 0 0 7px;
}

.subtitle {
  color: #64748b;
  font-size: 14px;
  margin: 0 0 24px;
}

.form-group {
  margin-bottom: 19px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  font-size: 14px;
  color: #334155;
}

.form-group input {
  width: 100%;
  box-sizing: border-box;
  padding: 13px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 7px;
  font-size: 15px;
  outline: none;
  background: #ffffff;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-group input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.primary-button {
  width: 100%;
  padding: 13px;
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 7px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.primary-button:hover {
  background: #1d4ed8;
}

.primary-button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.separator {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 23px 0;
  color: #94a3b8;
}

.separator::before,
.separator::after {
  content: "";
  height: 1px;
  flex: 1;
  background: #e2e8f0;
}

.switch-text {
  text-align: center;
  color: #334155;
  font-size: 14px;
  margin: 0 0 22px;
}

.text-button {
  background: none;
  border: none;
  padding: 0;
  color: #2563eb;
  font-size: inherit;
  font-weight: 700;
  cursor: pointer;
}

.text-button:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

.info-box {
  padding: 15px;
  border-radius: 8px;
  background: #eff6ff;
  color: #475569;
  font-size: 13px;
  line-height: 1.6;
}

.info-box strong {
  color: #1d4ed8;
  font-size: 14px;
}

.info-box ul {
  padding-left: 20px;
  margin: 8px 0 0;
}

.info-box li {
  margin-bottom: 4px;
}

.message {
  padding: 12px;
  border-radius: 7px;
  font-size: 14px;
  margin-bottom: 18px;
}

.error-message {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.success-message {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.auth-footer {
  text-align: center;
  padding: 14px;
  background: #f8fafc;
  color: #64748b;
  font-size: 12px;
  border-top: 1px solid #e2e8f0;
}

@media (max-width: 480px) {
  .auth-body {
    padding: 22px 18px;
  }

  .auth-header h1 {
    font-size: 22px;
  }
}
</style>
