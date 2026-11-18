<template>
  <div
    class="student-dashboard"
    :class="{ 'has-student-sidebar': ['student', 'examiner'].includes(user?.role) }"
  >
    <!-- Student Sidebar -->
    <aside v-if="['student', 'examiner'].includes(user?.role)" class="student-sidebar">
      <div class="student-brand">
        <div class="brand-mark">EP</div>
        <div>
          <strong>ExamPortal</strong>
          <small>{{ user?.role === 'examiner' ? 'Examiner Workspace' : 'Student Workspace' }}</small>
        </div>
      </div>

      <div class="sidebar-section-label">WORKSPACE</div>

      <nav class="student-nav" aria-label="Dashboard navigation">
        <router-link
          v-if="user?.role === 'student'"
          to="/examinations"
          class="student-nav-item"
        >
          <span class="nav-icon">▤</span> Available Examinations
        </router-link>

        <router-link
          v-if="user?.role === 'student'"
          to="/bookings"
          class="student-nav-item"
        >
          <span class="nav-icon">▣</span> My Bookings
        </router-link>

        <a
          v-if="user?.role === 'student'"
          href="#published-results"
          class="student-nav-item"
          @click.prevent="scrollToResults"
        >
          <span class="nav-icon">▧</span> Results
        </a>

        <router-link
          v-if="user?.role === 'student'"
          to="/profile"
          class="student-nav-item"
        >
          <span class="nav-icon">♙</span> Edit Profile
        </router-link>

        <button
          v-if="user?.role === 'examiner'"
          type="button"
          class="student-nav-item nav-button"
          @click="goToExaminerSection('overview')"
        >
          <span class="nav-icon">▦</span> Dashboard Overview
        </button>

        <button
          v-if="user?.role === 'examiner'"
          type="button"
          class="student-nav-item nav-button"
          @click="goToExaminerSection('examinations')"
        >
          <span class="nav-icon">▤</span> Assigned Examinations
        </button>

        <button
          v-if="user?.role === 'examiner'"
          type="button"
          class="student-nav-item nav-button"
          @click="goToExaminerSection('slots')"
        >
          <span class="nav-icon">▣</span> Examination Slots
        </button>

        <button
          v-if="user?.role === 'examiner'"
          type="button"
          class="student-nav-item nav-button"
          @click="goToExaminerSection('students')"
        >
          <span class="nav-icon">◔</span> Booked Students
        </button>

        <button
          v-if="user?.role === 'examiner'"
          type="button"
          class="student-nav-item nav-button"
          @click="goToExaminerSection('evaluations')"
        >
          <span class="nav-icon">✓</span> Student Evaluations
        </button>

        <button
          v-if="user?.role === 'examiner'"
          type="button"
          class="student-nav-item nav-button"
          @click="goToExaminerSection('completed')"
        >
          <span class="nav-icon">◫</span> Completed Examinations
        </button>
      </nav>

      <div class="student-sidebar-footer">
        <div class="student-user">
          <div class="student-avatar">
            {{ firstName.charAt(0).toUpperCase() }}
          </div>

          <div class="student-user-meta">
            <strong>{{ user?.name || (user?.role === 'examiner' ? 'Examiner' : 'Student') }}</strong>
            <small>{{ user?.email || (user?.role === 'examiner' ? 'Examiner account' : 'Student account') }}</small>
          </div>
        </div>

        <button
          v-if="user?.role === 'examiner' || user?.role === 'student'"
          class="student-signout"
          type="button"
          @click="signOut"
        >
          <span>↪</span> Sign Out
        </button>
      </div>
    </aside>

    <!-- Main Dashboard -->
    <main class="student-main-content">
      <div v-if="error" class="alert alert-warning">
        {{ error }}
      </div>

      <div v-if="loading" class="text-secondary py-4">
        Loading your dashboard…
      </div>

      <!-- STUDENT DASHBOARD -->
      <template v-else-if="user?.role === 'student'">
        <!-- Statistics -->
        <div class="row g-3 mb-4">
          <div class="col-6 col-xl">
            <div class="stat-card h-100">
              <div class="stat-label">Available examinations</div>
              <div class="stat-value">{{ availableExams.length }}</div>
              <div class="stat-note">Published catalogue</div>
            </div>
          </div>

          <div class="col-6 col-xl">
            <div class="stat-card h-100">
              <div class="stat-label">Available slots</div>
              <div class="stat-value">{{ availableSlots.length }}</div>
              <div class="stat-note">Seats currently open</div>
            </div>
          </div>

          <div class="col-6 col-xl">
            <div class="stat-card h-100">
              <div class="stat-label">Upcoming examinations</div>
              <div class="stat-value">{{ upcomingBookings.length }}</div>
              <div class="stat-note">Your future bookings</div>
            </div>
          </div>

          <div class="col-6 col-xl">
            <div class="stat-card h-100">
              <div class="stat-label">Booked slots</div>
              <div class="stat-value">{{ activeBookings.length }}</div>
              <div class="stat-note">Active reservations</div>
            </div>
          </div>

          <div class="col-6 col-xl">
            <div class="stat-card h-100">
              <div class="stat-label">Published results</div>
              <div class="stat-value">{{ results.length }}</div>
              <div class="stat-note">Ready to view</div>
            </div>
          </div>
        </div>

        <!-- Upcoming Exams and Quick Actions -->
        <div class="row g-4 mb-4">
          <div class="col-lg-7">
            <section class="card panel-card h-100">
              <div
                class="card-header bg-white d-flex justify-content-between align-items-center"
              >
                <h2 class="h5 mb-0">Upcoming examinations</h2>
                <router-link class="small" to="/bookings">
                  All bookings
                </router-link>
              </div>

              <div class="list-group list-group-flush">
                <div
                  v-for="b in upcomingBookings.slice(0, 5)"
                  :key="b.id"
                  class="list-group-item p-3 d-flex justify-content-between align-items-center gap-3"
                >
                  <div>
                    <div class="fw-semibold">
                      {{ b.examination_name }}
                    </div>

                    <div class="small text-secondary">
                      {{ b.course_name || 'Course' }}
                      · {{ b.exam_date }}
                      · {{ b.start_time }}–{{ b.end_time }}
                    </div>
                  </div>

                  <span class="badge text-bg-primary">
                    {{ b.status }}
                  </span>
                </div>

                <div
                  v-if="!upcomingBookings.length"
                  class="p-4 text-secondary"
                >
                  You have no upcoming booked examinations. Browse the catalogue
                  to find an available slot.
                </div>
              </div>
            </section>
          </div>

          <div class="col-lg-5">
            <section class="card panel-card h-100">
              <div class="card-header bg-white">
                <h2 class="h5 mb-0">Quick actions</h2>
              </div>

              <div class="card-body d-grid gap-2">
                <router-link class="quick-action" to="/examinations">
                  <span>Search and book an examination</span>
                  <span>↗</span>
                </router-link>

                <router-link class="quick-action" to="/bookings">
                  <span>View booking history and cancel</span>
                  <span>↗</span>
                </router-link>

                <a
                  class="quick-action"
                  href="#published-results"
                  @click.prevent="scrollToResults"
                >
                  <span>View published results &amp; remarks</span>
                  <span>↓</span>
                </a>

                <button class="quick-action" type="button" @click="requestExportHistory">
                  <span>Export examination history</span>
                  <span>↓</span>
                </button>

                <router-link class="quick-action" to="/profile">
                  <span>Edit my profile</span>
                  <span>↗</span>
                </router-link>
              </div>
            </section>
          </div>
        </div>

        <!-- Available Examinations and Results -->
        <div class="row g-4">
          <div class="col-lg-6">
            <section class="card panel-card h-100">
              <div
                class="card-header bg-white d-flex justify-content-between align-items-center"
              >
                <h2 class="h5 mb-0">Available examinations</h2>
                <router-link class="small" to="/examinations">
                  Search all
                </router-link>
              </div>

              <div class="list-group list-group-flush">
                <div
                  v-for="exam in availableExams.slice(0, 5)"
                  :key="exam.id"
                  class="list-group-item p-3 d-flex justify-content-between gap-3"
                >
                  <div>
                    <div class="fw-semibold">
                      {{ exam.examination_name }}
                    </div>

                    <div class="small text-secondary">
                      {{ exam.course_code }}
                      · {{ exam.course_name }}
                      · {{ exam.examination_type }}
                    </div>
                  </div>

                  <span class="badge text-bg-light align-self-start">
                    {{ exam.examination_status }}
                  </span>
                </div>

                <div
                  v-if="!availableExams.length"
                  class="p-4 text-secondary"
                >
                  No examinations are listed right now.
                </div>
              </div>
            </section>
          </div>

          <div class="col-lg-6" id="published-results">
            <section class="card panel-card h-100">
              <div class="card-header bg-white">
                <h2 class="h5 mb-0">
                  Published results &amp; evaluation remarks
                </h2>
              </div>

              <div class="table-responsive">
                <table class="table align-middle mb-0">
                  <thead>
                    <tr>
                      <th>Examination</th>
                      <th>Marks</th>
                      <th>Remarks</th>
                    </tr>
                  </thead>

                  <tbody>
                    <tr
                      v-for="(r, i) in results.slice(0, 5)"
                      :key="`${r.examination_name}-${i}`"
                    >
                      <td>
                        <div class="fw-semibold">
                          {{ r.examination_name }}
                        </div>

                        <div class="small text-secondary">
                          {{ r.course_name }}
                        </div>
                      </td>

                      <td>
                        {{ r.total_marks }} / {{ r.maximum_marks }}
                      </td>

                      <td class="small">
                        {{ r.remarks || 'No remarks' }}
                      </td>
                    </tr>

                    <tr v-if="!results.length">
                      <td
                        colspan="3"
                        class="text-secondary text-center py-4"
                      >
                        No results have been published for you yet.
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        </div>
      </template>

      <!-- ADMIN DASHBOARD -->
      <template v-else-if="user?.role === 'admin'">
        <div class="row g-3 mb-4">
          <div
            class="col-6 col-xl-3"
            v-for="s in adminStats"
            :key="s.label"
          >
            <div class="stat-card h-100">
              <div class="stat-label">{{ s.label }}</div>
              <div class="stat-value">{{ s.value }}</div>
              <div class="stat-note">{{ s.note }}</div>
            </div>
          </div>
        </div>

        <section class="card panel-card">
          <div class="card-header bg-white">
            <h2 class="h5 mb-0">Administration</h2>
          </div>

          <div class="card-body">
            <p class="text-secondary">
              Manage courses, examiners, examinations and result publication.
            </p>

            <router-link class="btn btn-primary" to="/admin">
              Open administration
            </router-link>
          </div>
        </section>
      </template>

      <!-- EXAMINER DASHBOARD -->
      <template v-else-if="user?.role === 'examiner'">
        <div class="row g-3 mb-4" id="examiner-overview">
          <div class="col-6 col-xl-3">
            <div class="stat-card h-100">
              <div class="stat-label">Assigned examinations</div>
              <div class="stat-value">{{ exams.length }}</div>
              <div class="stat-note">Exams assigned to you</div>
            </div>
          </div>

          <div class="col-6 col-xl-3">
            <div class="stat-card h-100">
              <div class="stat-label">Created slots</div>
              <div class="stat-value">{{ examinerSlots.length }}</div>
              <div class="stat-note">Including past slots</div>
            </div>
          </div>

          <div class="col-6 col-xl-3">
            <div class="stat-card h-100">
              <div class="stat-label">Booked students</div>
              <div class="stat-value">{{ bookedStudentCount }}</div>
              <div class="stat-note">Active bookings</div>
            </div>
          </div>

          <div class="col-6 col-xl-3">
            <div class="stat-card h-100">
              <div class="stat-label">Pending evaluations</div>
              <div class="stat-value">{{ pendingEvaluationCount }}</div>
              <div class="stat-note">Students awaiting marks</div>
            </div>
          </div>
        </div>

        <div
          v-if="examinerMessage"
          class="alert"
          :class="examinerError ? 'alert-danger' : 'alert-success'"
        >
          {{ examinerMessage }}
        </div>

        <div class="row g-3 mb-4">
          <div class="col-6 col-xl-3">
            <div class="stat-card h-100">
              <div class="stat-label">Available examinations</div>
              <div class="stat-value">{{ availableExams.length }}</div>
              <div class="stat-note">Open to book</div>
            </div>
          </div>

          <div class="col-6 col-xl-3">
            <div class="stat-card h-100">
              <div class="stat-label">Available slots</div>
              <div class="stat-value">{{ availableSlots.length }}</div>
              <div class="stat-note">Seats currently open</div>
            </div>
          </div>

          <div class="col-6 col-xl-3">
            <div class="stat-card h-100">
              <div class="stat-label">Upcoming examinations</div>
              <div class="stat-value">{{ upcomingBookings.length }}</div>
              <div class="stat-note">Future bookings</div>
            </div>
          </div>

          <div class="col-6 col-xl-3">
            <div class="stat-card h-100">
              <div class="stat-label">Published results</div>
              <div class="stat-value">{{ results.length }}</div>
              <div class="stat-note">Available to review</div>
            </div>
          </div>
        </div>

        <div class="row g-4 mb-4">
          <div class="col-lg-7">
            <section class="card panel-card h-100">
              <div class="card-header bg-white d-flex justify-content-between align-items-center">
                <h3 class="h5 mb-0">Available examinations</h3>
                <input
                  v-model="examSearchTerm"
                  class="form-control"
                  style="max-width: 220px;"
                  placeholder="Search examinations"
                >
              </div>

              <div class="list-group list-group-flush">
                <div
                  v-for="exam in filteredAvailableExams"
                  :key="exam.id"
                  class="list-group-item p-3 d-flex justify-content-between align-items-center gap-3"
                >
                  <div>
                    <div class="fw-semibold">{{ exam.examination_name }}</div>
                    <div class="small text-secondary">
                      {{ exam.course_name || 'Course' }} · {{ exam.examination_type }} · {{ exam.maximum_marks }} marks
                    </div>
                  </div>

                  <div class="d-flex align-items-center gap-2 flex-wrap">
                    <span class="badge text-bg-light">{{ exam.examination_status }}</span>
                    <button
                      class="btn btn-sm btn-primary"
                      type="button"
                      @click="bookSlot(exam)"
                      :disabled="exam.examination_status !== 'Booking Open'"
                    >
                      Book slot
                    </button>
                  </div>
                </div>

                <div v-if="!filteredAvailableExams.length" class="p-4 text-secondary">
                  No matching examinations are available right now.
                </div>
              </div>
            </section>
          </div>

          <div class="col-lg-5">
            <section class="card panel-card h-100">
              <div class="card-header bg-white">
                <h3 class="h5 mb-0">Quick actions</h3>
              </div>

              <div class="card-body d-grid gap-2">
                <button class="quick-action" type="button" @click="openSlotForm">
                  <span>Create a new examination slot</span>
                  <span>↗</span>
                </button>

                <button
                  class="quick-action"
                  type="button"
                  @click="() => examinerSlots.length && viewStudents(examinerSlots[0])"
                  :disabled="!examinerSlots.length"
                >
                  <span>Review booked students</span>
                  <span>↗</span>
                </button>

                <router-link class="quick-action" to="/profile">
                  <span>Edit profile</span>
                  <span>↗</span>
                </router-link>

                <button
                  class="quick-action"
                  type="button"
                  @click="() => (selectedSlot = null, slotStudents = [])"
                >
                  <span>Clear selected slot</span>
                  <span>✓</span>
                </button>
              </div>
            </section>
          </div>
        </div>

        <section class="card panel-card mb-4">
          <div class="card-header bg-white">
            <h3 class="h5 mb-0">Your booked examination slots</h3>
          </div>

          <div class="table-responsive">
            <table class="table align-middle mb-0">
              <thead>
                <tr>
                  <th>Examination</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="booking in upcomingBookings" :key="booking.id">
                  <td>{{ booking.examination_name }}</td>
                  <td>{{ booking.exam_date }}</td>
                  <td>{{ booking.start_time }}–{{ booking.end_time }}</td>
                  <td><span class="badge text-bg-light">{{ booking.status }}</span></td>
                  <td>
                    <button class="btn btn-sm btn-outline-danger" type="button" @click="cancelBooking(booking)">
                      Cancel
                    </button>
                  </td>
                </tr>
                <tr v-if="!upcomingBookings.length">
                  <td colspan="5" class="text-center text-secondary py-4">No booked slots yet.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="card panel-card mb-4">
          <div class="card-header bg-white">
            <h3 class="h5 mb-0">Published results &amp; evaluation remarks</h3>
          </div>

          <div class="table-responsive">
            <table class="table align-middle mb-0">
              <thead>
                <tr>
                  <th>Examination</th>
                  <th>Marks</th>
                  <th>Remarks</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(result, index) in results.slice(0, 5)" :key="`${result.examination_name}-${index}`">
                  <td>
                    <div class="fw-semibold">{{ result.examination_name }}</div>
                    <div class="small text-secondary">{{ result.course_name }}</div>
                  </td>
                  <td>{{ result.total_marks }} / {{ result.maximum_marks }}</td>
                  <td class="small">{{ result.remarks || 'No remarks' }}</td>
                </tr>
                <tr v-if="!results.length">
                  <td colspan="3" class="text-secondary text-center py-4">No published results are available yet.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section id="examiner-examinations" class="card panel-card h-100">
          <div class="card-header bg-white d-flex justify-content-between align-items-center">
            <h3 class="h5 mb-0">Assigned examinations</h3>
            <span class="badge text-bg-light">{{ exams.length }} total</span>
          </div>

          <div class="list-group list-group-flush">
            <div
              v-for="exam in exams"
              :key="exam.id"
              class="list-group-item p-3 d-flex justify-content-between align-items-center gap-3"
            >
              <div>
                <div class="fw-semibold">{{ exam.examination_name }}</div>
                <div class="small text-secondary">
                  {{ exam.course_name || 'Course' }} · {{ exam.maximum_marks }} marks
                </div>
              </div>

              <div class="d-flex align-items-center gap-2 flex-wrap">
                <span class="badge text-bg-light">{{ exam.examination_status }}</span>
                <button
                  class="btn btn-sm btn-outline-primary"
                  @click="createSlotForExam(exam)"
                  :disabled="exam.examination_status !== 'Slot Creation'"
                >
                  Create slot
                </button>
                <button
                  class="btn btn-sm btn-outline-success"
                  @click="completeExam(exam)"
                  :disabled="exam.examination_status === 'Completed'"
                >
                  Mark completed
                </button>
              </div>
            </div>

            <div v-if="!exams.length" class="p-4 text-secondary">
              No examinations assigned yet. Ask Admin to assign you to an examination.
            </div>
          </div>
        </section>

        <!-- Examiner Slots -->
        <section id="examiner-slots" class="card panel-card">
          <div class="card-header bg-white">
            <h3 class="h5 mb-0">Your examination slots</h3>
          </div>

          <div class="table-responsive">
            <table class="table align-middle mb-0">
              <thead>
                <tr>
                  <th>Examination / date</th>
                  <th>Time</th>
                  <th>Students booked</th>
                  <th>Pending evaluations</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                <tr v-for="slot in examinerSlots" :key="slot.id">
                  <td>
                    <div class="fw-semibold">
                      {{ slot.examination_name }}
                    </div>
                    <div class="small text-secondary">
                      {{ slot.exam_date }}
                    </div>
                  </td>

                  <td>{{ slot.start_time }}–{{ slot.end_time }}</td>
                  <td>{{ slot.booked_students || 0 }}</td>
                  <td>{{ slot.pending_evaluations || 0 }}</td>

                  <td>
                    <span class="badge text-bg-light">
                      {{ slot.status }}
                    </span>
                  </td>

                  <td>
                    <button
                      class="btn btn-sm btn-outline-primary"
                      @click="viewStudents(slot)"
                    >
                      View / evaluate
                    </button>

                    <button
                      class="btn btn-sm btn-outline-secondary mt-1"
                      @click="editSlot(slot)"
                      :disabled="!canEditSlot(slot)"
                    >
                      Edit
                    </button>
                  </td>
                </tr>

                <tr v-if="!examinerSlots.length">
                  <td colspan="6" class="text-center text-secondary py-4">
                    No slots created yet.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- Students in Selected Slot -->
        <section v-if="selectedSlot" id="examiner-students" class="card panel-card mt-4">
          <div
            class="card-header bg-white d-flex justify-content-between align-items-center"
          >
            <h3 class="h5 mb-0">
              Booked students · {{ selectedSlot.examination_name }}
            </h3>

            <button
              class="btn btn-sm btn-outline-secondary"
              @click="selectedSlot = null; slotStudents = []"
            >
              Close
            </button>
          </div>

          <div class="table-responsive">
            <table class="table align-middle mb-0">
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Email</th>
                  <th>Booking</th>
                  <th>Evaluation</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                <tr
                  v-for="student in slotStudents"
                  :key="student.booking_id"
                >
                  <td>{{ student.student_name }}</td>
                  <td>{{ student.email }}</td>
                  <td>{{ student.booking_status }}</td>

                  <td>
                    {{
                      student.evaluation_id
                        ? `${student.total_marks} marks`
                        : 'Pending'
                    }}
                  </td>

                  <td>
                    <button
                      class="btn btn-sm btn-primary"
                      @click="openEvaluation(student)"
                      :disabled="
                        !!student.evaluation_id ||
                        !['Booked', 'Completed'].includes(student.booking_status)
                      "
                    >
                      Evaluate
                    </button>
                  </td>
                </tr>

                <tr v-if="!slotStudents.length">
                  <td colspan="5" class="text-center text-secondary py-4">
                    No students are booked in this slot.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section id="examiner-completed" class="card panel-card mt-4">
          <div class="card-header bg-white">
            <h3 class="h5 mb-0">Completed examinations</h3>
          </div>

          <div class="list-group list-group-flush">
            <div
              v-for="exam in completedExams"
              :key="exam.id"
              class="list-group-item p-3 d-flex justify-content-between align-items-center gap-3"
            >
              <div>
                <div class="fw-semibold">{{ exam.examination_name }}</div>
                <div class="small text-secondary">
                  {{ exam.course_name || 'Course' }}
                </div>
              </div>
              <span class="badge text-bg-success">Completed</span>
            </div>

            <div v-if="!completedExams.length" class="p-4 text-secondary">
              No examinations have been marked completed yet.
            </div>
          </div>
        </section>

        <!-- Keep your existing slot modal and evaluation modal here unchanged -->
        <div v-if="slotFormOpen" class="modal-backdrop-custom">
          <div class="card slot-modal shadow-lg">
            <div class="card-body">
              <div
                class="d-flex justify-content-between align-items-center mb-3"
              >
                <h3 class="h5 mb-0">
                  {{ slotForm.id ? 'Update slot' : 'Create examination slot' }}
                </h3>

                <button
                  class="btn-close"
                  type="button"
                  @click="slotFormOpen = false"
                ></button>
              </div>

              <form @submit.prevent="saveSlot">
                <label class="form-label">Examination</label>

                <select
                  v-model="slotForm.examination_id"
                  class="form-select mb-3"
                  required
                >
                  <option value="" disabled>
                    Select assigned examination
                  </option>

                  <option
                    v-for="exam in slotEligibleExams"
                    :key="exam.id"
                    :value="exam.id"
                  >
                    {{ exam.examination_name }}
                  </option>
                </select>

                <div class="row g-2">
                  <div class="col-6">
                    <label class="form-label">Date</label>
                    <input
                      v-model="slotForm.exam_date"
                      type="date"
                      class="form-control"
                      required
                    />
                  </div>

                  <div class="col-6">
                    <label class="form-label">Capacity</label>
                    <input
                      v-model.number="slotForm.maximum_capacity"
                      type="number"
                      min="1"
                      class="form-control"
                      required
                    />
                  </div>

                  <div class="col-6">
                    <label class="form-label">Start time</label>
                    <input
                      v-model="slotForm.start_time"
                      type="time"
                      class="form-control"
                      required
                    />
                  </div>

                  <div class="col-6">
                    <label class="form-label">End time</label>
                    <input
                      v-model="slotForm.end_time"
                      type="time"
                      class="form-control"
                      required
                    />
                  </div>
                </div>

                <label class="form-label mt-3">
                  Meeting link (optional)
                </label>

                <input
                  v-model="slotForm.meeting_link"
                  type="url"
                  class="form-control mb-3"
                />

                <div class="d-flex gap-2">
                  <button class="btn btn-primary" type="submit">
                    Save slot
                  </button>

                  <button
                    class="btn btn-outline-secondary"
                    type="button"
                    @click="slotFormOpen = false"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>

        <!-- Evaluation Modal -->
        <div v-if="evaluationStudent" class="modal-backdrop-custom">
          <div class="card slot-modal shadow-lg">
            <div class="card-body">
              <div
                class="d-flex justify-content-between align-items-center mb-3"
              >
                <h3 class="h5 mb-0">
                  Evaluate {{ evaluationStudent.student_name }}
                </h3>

                <button
                  class="btn-close"
                  type="button"
                  @click="evaluationStudent = null"
                ></button>
              </div>

              <div
                v-if="!evaluationRubrics.length"
                class="alert alert-warning"
              >
                Admin has not added rubric criteria for this examination yet.
              </div>

              <form @submit.prevent="submitEvaluation">
                <div
                  v-for="rubric in evaluationRubrics"
                  :key="rubric.id"
                  class="border rounded p-3 mb-2"
                >
                  <div class="fw-semibold">
                    {{ rubric.criterion_name }}
                    <span class="small text-secondary">
                      (max {{ rubric.maximum_marks }})
                    </span>
                  </div>

                  <div class="small text-secondary mb-2">
                    {{ rubric.description }}
                  </div>

                  <input
                    v-model.number="evaluationMarks[rubric.id]"
                    type="number"
                    min="0"
                    :max="rubric.maximum_marks"
                    step="0.5"
                    class="form-control"
                    required
                  />
                </div>

                <label class="form-label mt-2">Remarks</label>

                <textarea
                  v-model="evaluationRemarks"
                  class="form-control mb-3"
                  rows="3"
                  placeholder="Feedback for the student"
                ></textarea>

                <button
                  class="btn btn-primary"
                  type="submit"
                  :disabled="!evaluationRubrics.length"
                >
                  Submit marks &amp; remarks
                </button>
              </form>
            </div>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<script>
import { api } from '../services/api'

export default {
  data: () => ({
    user: null,
    exams: [],
    slots: [],
    bookings: [],
    results: [],
    counts: {},
    loading: true,
    error: '',

    examinerSlots: [],
    selectedSlot: null,
    slotStudents: [],

    slotFormOpen: false,
    slotForm: {
      id: null,
      examination_id: '',
      exam_date: '',
      start_time: '',
      end_time: '',
      maximum_capacity: 1,
      meeting_link: ''
    },

    slotEligibleExams: [],
    evaluationStudent: null,
    evaluationRubrics: [],
    evaluationMarks: {},
    evaluationRemarks: '',

    examinerMenu: [
      { id: 'overview', label: 'Overview', icon: '▦' },
      { id: 'examinations', label: 'Examinations', icon: '▤' },
      { id: 'slots', label: 'Slots', icon: '▣' },
      { id: 'students', label: 'Students', icon: '◔' },
      { id: 'completed', label: 'Completed', icon: '✓' }
    ],
    activeExaminerSection: 'overview',
    examinerMessage: '',
    examinerError: false,
    examSearchTerm: ''
  }),

  computed: {
    firstName() {
      return (this.user?.name || 'student').split(' ')[0]
    },

    availableExams() {
      return this.exams.filter(
        exam =>
          !['Draft', 'Closed', 'Completed'].includes(
            exam.examination_status
          )
      )
    },

    availableSlots() {
      return this.slots.filter(
        slot =>
          slot.status === 'Available' &&
          Number(slot.available_seats) > 0
      )
    },

    activeBookings() {
      return this.bookings.filter(
        booking => booking.status === 'Booked'
      )
    },

    upcomingBookings() {
      const today = new Date().toISOString().slice(0, 10)

      return this.activeBookings
        .filter(booking => booking.exam_date >= today)
        .sort((a, b) =>
          `${a.exam_date} ${a.start_time}`.localeCompare(
            `${b.exam_date} ${b.start_time}`
          )
        )
    },

    adminStats() {
      return [
        {
          label: 'Courses',
          value: this.counts.courses || 0,
          note: 'Catalogue'
        },
        {
          label: 'Examinations',
          value: this.counts.examinations || 0,
          note: 'All courses'
        },
        {
          label: 'Students',
          value: this.counts.students || 0,
          note: 'Registered learners'
        },
        {
          label: 'Bookings',
          value: this.counts.bookings || 0,
          note: 'Booking records'
        }
      ]
    },

    bookedStudentCount() {
      return this.examinerSlots.reduce(
        (total, slot) => total + Number(slot.booked_students || 0),
        0
      )
    },

    pendingEvaluationCount() {
      return this.examinerSlots.reduce(
        (total, slot) => total + Number(slot.pending_evaluations || 0),
        0
      )
    },

    completedExams() {
      return this.exams.filter(
        exam => exam.examination_status === 'Completed'
      )
    },

    filteredAvailableExams() {
      const q = this.examSearchTerm.trim().toLowerCase()

      if (!q) {
        return this.availableExams
      }

      return this.availableExams.filter(exam =>
        [
          exam.examination_name,
          exam.course_name,
          exam.course_code,
          exam.examination_type,
          exam.examination_status
        ].some(value => String(value || '').toLowerCase().includes(q))
      )
    }
  },

  async mounted() {
    await this.loadDashboard()
  },

  methods: {
    async loadDashboard() {
      this.loading = true
      this.error = ''

      try {
        this.user = (await api.get('/auth/me')).data.user

        if (this.user.role === 'student') {
          const responses = await Promise.allSettled([
            api.get('/examinations'),
            api.get('/slots', { params: { available: 1 } }),
            api.get('/bookings'),
            api.get('/student/results')
          ])

          this.exams =
            responses[0].status === 'fulfilled'
              ? responses[0].value.data.items || []
              : []

          this.slots =
            responses[1].status === 'fulfilled'
              ? responses[1].value.data.items || []
              : []

          this.bookings =
            responses[2].status === 'fulfilled'
              ? responses[2].value.data.items || []
              : []

          this.results =
            responses[3].status === 'fulfilled'
              ? responses[3].value.data.items || []
              : []

          if (responses.every(response => response.status === 'rejected')) {
            this.error =
              'Dashboard data could not be loaded. Check that the backend is running and your session is active.'
          }
        } else if (this.user.role === 'admin') {
          this.counts =
            (await api.get('/admin/dashboard')).data.counts || {}
        } else if (this.user.role === 'examiner') {
          const [assignedExamsResponse, examinerSlotsResponse, examCatalogueResponse, slotCatalogueResponse, bookingsResponse, resultsResponse] = await Promise.allSettled([
            api.get('/examinations/assigned-to-me'),
            api.get('/examiner/slots'),
            api.get('/examinations'),
            api.get('/slots', { params: { available: 1 } }),
            api.get('/bookings'),
            api.get('/student/results')
          ])

          this.exams = assignedExamsResponse.status === 'fulfilled'
            ? assignedExamsResponse.value.data.items || []
            : []

          this.examinerSlots = examinerSlotsResponse.status === 'fulfilled'
            ? examinerSlotsResponse.value.data.items || []
            : []

          this.slots = slotCatalogueResponse.status === 'fulfilled'
            ? slotCatalogueResponse.value.data.items || []
            : []

          this.bookings = bookingsResponse.status === 'fulfilled'
            ? bookingsResponse.value.data.items || []
            : []

          this.results = resultsResponse.status === 'fulfilled'
            ? resultsResponse.value.data.items || []
            : []

          this.exams = this.exams.length
            ? this.exams
            : (examCatalogueResponse.status === 'fulfilled' ? examCatalogueResponse.value.data.items || [] : [])
        }
      } catch (error) {
        this.error =
          error.response?.data?.error ||
          'Could not load dashboard data. Please sign in again if your session has expired.'
      } finally {
        this.loading = false
      }
    },

    async refreshExaminer() {
      const [examsResponse, slotsResponse, bookingsResponse, resultsResponse, slotCatalogueResponse] = await Promise.allSettled([
        api.get('/examinations/assigned-to-me'),
        api.get('/examiner/slots'),
        api.get('/bookings'),
        api.get('/student/results'),
        api.get('/slots', { params: { available: 1 } })
      ])

      this.exams = examsResponse.status === 'fulfilled' ? examsResponse.value.data.items || [] : []
      this.examinerSlots = slotsResponse.status === 'fulfilled' ? slotsResponse.value.data.items || [] : []
      this.bookings = bookingsResponse.status === 'fulfilled' ? bookingsResponse.value.data.items || [] : []
      this.results = resultsResponse.status === 'fulfilled' ? resultsResponse.value.data.items || [] : []
      this.slots = slotCatalogueResponse.status === 'fulfilled' ? slotCatalogueResponse.value.data.items || [] : []
    },

    goToExaminerSection(sectionId) {
      this.activeExaminerSection = sectionId

      const sectionMap = {
        overview: 'examiner-overview',
        examinations: 'examiner-examinations',
        slots: 'examiner-slots',
        students: 'examiner-students',
        evaluations: 'examiner-students',
        completed: 'examiner-completed'
      }

      const element = document.getElementById(sectionMap[sectionId])

      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    },

    openSlotForm() {
      this.slotForm = {
        id: null,
        examination_id: '',
        exam_date: '',
        start_time: '',
        end_time: '',
        maximum_capacity: 1,
        meeting_link: ''
      }

      this.slotEligibleExams = this.exams.filter(
        exam => exam.examination_status === 'Slot Creation'
      )

      this.slotFormOpen = true
    },

    createSlotForExam(exam) {
      this.openSlotForm()
      this.slotForm.examination_id = exam.id
    },

    canEditSlot(slot) {
      return (
        slot.status === 'Available' &&
        Number(slot.booked_students || 0) === 0 &&
        slot.examination_status === 'Slot Creation'
      )
    },

    editSlot(slot) {
      this.slotEligibleExams = this.exams.filter(
        exam => exam.examination_status === 'Slot Creation'
      )

      this.slotForm = {
        id: slot.id,
        examination_id: slot.examination_id,
        exam_date: slot.exam_date,
        start_time: slot.start_time,
        end_time: slot.end_time,
        maximum_capacity: slot.maximum_capacity,
        meeting_link: slot.meeting_link || ''
      }

      this.slotFormOpen = true
    },

    async saveSlot() {
      try {
        const payload = { ...this.slotForm }
        delete payload.id

        if (this.slotForm.id) {
          await api.put(`/slots/${this.slotForm.id}`, payload)
        } else {
          await api.post('/slots', payload)
        }

        const wasUpdate = Boolean(this.slotForm.id)

        this.slotFormOpen = false
        this.examinerError = false
        this.examinerMessage = wasUpdate
          ? 'Slot updated successfully.'
          : 'Slot created successfully.'

        await this.refreshExaminer()
      } catch (error) {
        this.examinerError = true
        this.examinerMessage =
          error.response?.data?.error || 'Could not save slot.'
      }
    },

    async viewStudents(slot) {
      this.selectedSlot = slot

      try {
        this.slotStudents =
          (await api.get(`/examiner/slots/${slot.id}/students`))
            .data.items || []
      } catch (error) {
        this.examinerError = true
        this.examinerMessage =
          error.response?.data?.error || 'Could not load students.'
      }
    },

    async openEvaluation(student) {
      this.evaluationStudent = student
      this.evaluationMarks = {}
      this.evaluationRemarks = ''

      try {
        const response = await api.get(
          `/examinations/${this.selectedSlot.examination_id}/rubrics`
        )

        this.evaluationRubrics = response.data.items || []

        this.evaluationRubrics.forEach(rubric => {
          this.evaluationMarks[rubric.id] = 0
        })
      } catch (error) {
        this.evaluationRubrics = []
        this.examinerError = true
        this.examinerMessage =
          error.response?.data?.error || 'Could not load rubrics.'
      }
    },

    async submitEvaluation() {
      try {
        const criteria = this.evaluationRubrics.map(rubric => ({
          rubric_id: rubric.id,
          marks: Number(this.evaluationMarks[rubric.id] || 0)
        }))

        await api.post(
          `/bookings/${this.evaluationStudent.booking_id}/evaluation`,
          {
            criteria,
            remarks: this.evaluationRemarks
          }
        )

        this.evaluationStudent = null
        this.examinerError = false
        this.examinerMessage = 'Evaluation submitted successfully.'

        await this.viewStudents(this.selectedSlot)
        await this.refreshExaminer()
      } catch (error) {
        this.examinerError = true
        this.examinerMessage =
          error.response?.data?.error || 'Could not submit evaluation.'
      }
    },

    async completeExam(exam) {
      if (
        !window.confirm(
          `Mark "${exam.examination_name}" as completed?`
        )
      ) {
        return
      }

      try {
        await api.post(`/examiner/examinations/${exam.id}/complete`)

        this.examinerError = false
        this.examinerMessage = 'Examination marked as completed.'

        await this.refreshExaminer()
      } catch (error) {
        this.examinerError = true
        this.examinerMessage =
          error.response?.data?.error ||
          'Could not complete examination.'
      }
    },

    async bookSlot(exam) {
      if (!exam || exam.examination_status !== 'Booking Open') {
        this.examinerError = true
        this.examinerMessage = 'This examination is not currently open for booking.'
        return
      }

      const availableSlot = this.slots.find(slot =>
        slot.examination_id === exam.id &&
        slot.status === 'Available' &&
        Number(slot.available_seats) > 0
      )

      if (!availableSlot) {
        this.examinerError = true
        this.examinerMessage = 'No open slot is available for this examination yet.'
        return
      }

      try {
        await api.post(`/slots/${availableSlot.id}/book`)
        this.examinerError = false
        this.examinerMessage = 'Examination slot booked successfully.'
        await this.loadDashboard()
      } catch (error) {
        this.examinerError = true
        this.examinerMessage = error.response?.data?.error || 'Could not book this slot.'
      }
    },

    async cancelBooking(booking) {
      if (!booking) return

      if (!window.confirm(`Cancel booking for ${booking.examination_name}?`)) {
        return
      }

      try {
        await api.post(`/bookings/${booking.id}/cancel`)
        this.examinerError = false
        this.examinerMessage = 'Booking cancelled successfully.'
        await this.loadDashboard()
      } catch (error) {
        this.examinerError = true
        this.examinerMessage = error.response?.data?.error || 'Could not cancel booking.'
      }
    },

    async requestExportHistory() {
      try {
        this.examinerError = false
        this.examinerMessage = 'Preparing your examination history export…'

        const queued = await api.post('/exports')
        const jobId = queued.data.job_id
        let status = queued.data.status
        let attempts = 0

        while (['Pending', 'Processing'].includes(status) && attempts < 40) {
          await new Promise(resolve => setTimeout(resolve, 1000))
          const statusResponse = await api.get(`/exports/${jobId}`)
          status = statusResponse.data.job?.status || status
          attempts += 1
        }

        if (status !== 'Completed') {
          const jobResponse = await api.get(`/exports/${jobId}`)
          throw new Error(jobResponse.data.job?.error_message || 'Export could not be completed.')
        }

        const baseUrl = (api.defaults.baseURL || 'http://localhost:5000/api').replace(/\/api$/, '')
        window.open(`${baseUrl}/api/exports/${jobId}/download`, '_blank')
        this.examinerMessage = 'Your examination history export is ready.'
      } catch (error) {
        this.examinerError = true
        this.examinerMessage = error.response?.data?.error || error.message || 'Could not export examination history.'
      }
    },

    scrollToResults() {
      document
        .getElementById('published-results')
        ?.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        })
    },

    async signOut() {
      try {
        await api.post('/auth/logout')
      } catch (error) {
        // Ignore logout errors and still return the user to the login page.
      } finally {
        this.$router.push('/login')
      }
    }
  }
}
</script>

<style scoped>
.student-dashboard {
  color: #1e293b;
  padding-bottom: 24px;
}

.student-main-content {
  min-width: 0;
}

.student-sidebar {
  display: flex;
  flex-direction: column;
  position: fixed;
  z-index: 1020;
  inset: 0 auto 0 0;
  width: 258px;
  padding: 22px 15px 16px;
  background: #10233f;
  color: #dbe7f6;
  box-shadow: 5px 0 24px rgba(15, 23, 42, 0.08);
}

.student-brand {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 3px 9px 26px;
  color: #fff;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  color: #fff;
  background: #2563eb;
  font-weight: 800;
  letter-spacing: -0.5px;
}

.student-brand strong,
.student-brand small,
.student-user-meta strong,
.student-user-meta small {
  display: block;
}

.student-brand strong {
  font-size: 1rem;
}

.student-brand small {
  margin-top: 3px;
  color: #9fb2cd;
  font-size: 0.72rem;
}

.sidebar-section-label {
  padding: 7px 11px 10px;
  color: #8297b5;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 1.4px;
}

.student-nav {
  display: grid;
  gap: 5px;
}

.student-nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 12px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: #bdcce0;
  text-decoration: none;
  font-size: 0.87rem;
  font-weight: 600;
  transition: background 0.18s, color 0.18s;
  text-align: left;
  font-family: inherit;
  width: 100%;
}

.student-nav-item:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.student-nav-item:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.student-nav-item.router-link-exact-active {
  color: #fff;
  background: #2563eb;
  box-shadow: 0 5px 14px rgba(37, 99, 235, 0.25);
}

.nav-icon {
  display: inline-grid;
  place-items: center;
  width: 20px;
  font-size: 1.05rem;
}

.student-sidebar-footer {
  margin-top: auto;
  border-top: 1px solid rgba(203, 213, 225, 0.16);
  padding: 16px 4px 0;
}

.student-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 6px 13px;
  min-width: 0;
}

.student-avatar {
  display: grid;
  place-items: center;
  flex: 0 0 35px;
  width: 35px;
  height: 35px;
  border-radius: 50%;
  color: #fff;
  background: #334f75;
  font-weight: 800;
}

.student-user-meta {
  min-width: 0;
}

.student-user-meta strong {
  overflow: hidden;
  color: #fff;
  font-size: 0.8rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.student-user-meta small {
  overflow: hidden;
  margin-top: 3px;
  color: #9fb2cd;
  font-size: 0.69rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.student-signout {
  width: 100%;
  padding: 9px 11px;
  border: 1px solid rgba(203, 213, 225, 0.18);
  border-radius: 8px;
  background: transparent;
  color: #dbe7f6;
  text-align: left;
  font-size: 0.85rem;
  font-weight: 600;
}

.student-signout:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.has-student-sidebar .student-main-content {
  margin-left: 278px;
}

@media (max-width: 900px) {
  .student-sidebar {
    width: 218px;
  }

  .has-student-sidebar .student-main-content {
    margin-left: 236px;
  }
}

@media (max-width: 650px) {
  .student-sidebar {
    position: static;
    width: auto;
    margin: -12px -12px 22px;
    padding: 14px 12px;
    border-radius: 12px;
  }

  .student-brand {
    padding-bottom: 12px;
  }

  .sidebar-section-label,
  .student-sidebar-footer {
    display: none;
  }

  .student-nav {
    display: flex;
    gap: 6px;
    overflow-x: auto;
    padding-bottom: 3px;
  }

  .student-nav-item {
    flex: 0 0 auto;
    padding: 9px 10px;
    font-size: 0.78rem;
  }

  .nav-icon {
    display: none;
  }

  .has-student-sidebar .student-main-content {
    margin-left: 0;
  }
}

.page-title {
  color: #17365d;
  font-size: clamp(1.7rem, 3vw, 2.2rem);
  font-weight: 750;
  letter-spacing: -0.5px;
}

.eyebrow {
  color: #2563eb;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 1.5px;
  margin-bottom: 8px;
}

.stat-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 3px 12px rgba(30, 58, 95, 0.04);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(30, 58, 95, 0.09);
}

.stat-label {
  color: #64748b;
  font-size: 0.82rem;
  font-weight: 600;
  line-height: 1.5;
}

.stat-value {
  color: #1d4ed8;
  font-size: 2rem;
  font-weight: 750;
  margin: 8px 0 4px;
}

.stat-note {
  color: #94a3b8;
  font-size: 0.78rem;
}

.panel-card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 14px rgba(30, 58, 95, 0.04);
}

.panel-card .card-header {
  padding: 17px 20px;
  border-bottom: 1px solid #eaf0f6;
}

.panel-card .card-header h2,
.panel-card .card-header h3 {
  color: #1e3a5f;
  font-weight: 700;
}

.panel-card .list-group-item {
  border-color: #edf2f7;
}

.panel-card .list-group-item:hover {
  background: #f8fbff;
}

.quick-action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 15px;
  border: 1px solid #e2e8f0;
  border-radius: 9px;
  color: #334155;
  background: #fff;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.2s;
}

.quick-action:hover {
  color: #1d4ed8;
  border-color: #93c5fd;
  background: #eff6ff;
}

.student-dashboard .btn-primary {
  background: #2563eb;
  border-color: #2563eb;
}

.student-dashboard .btn-primary:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.student-dashboard .table th {
  color: #64748b;
  background: #f8fafc;
  font-size: 0.8rem;
  font-weight: 700;
  white-space: nowrap;
}

.student-dashboard .table td {
  font-size: 0.875rem;
}

.student-dashboard .badge {
  font-weight: 600;
  padding: 6px 9px;
}

.modal-backdrop-custom {
  position: fixed;
  z-index: 1050;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.55);
  overflow-y: auto;
}

.slot-modal {
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  border: 0;
  border-radius: 14px;
}

@media (max-width: 576px) {
  .stat-card {
    padding: 14px;
  }

  .stat-value {
    font-size: 1.6rem;
  }

  .panel-card .card-header {
    padding: 14px;
  }

  .page-title {
    font-size: 1.6rem;
  }

  .quick-action {
    padding: 12px;
    font-size: 0.83rem;
  }
}
</style>