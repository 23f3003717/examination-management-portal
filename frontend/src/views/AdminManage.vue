<template>
  <div class="admin-page">
    <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4">
      <div>
        <div class="eyebrow">ADMINISTRATION</div>
        <h1 class="page-title">Admin control centre</h1>
        <p class="text-secondary mb-0">
          Manage the full examination lifecycle from one dashboard.
        </p>
      </div>
      <button class="btn btn-outline-primary" @click="loadAll" :disabled="loading">
        {{ loading ? 'Refreshing...' : 'Refresh data' }}
      </button>
    </div>

    <div
      v-if="message"
      class="alert"
      :class="messageType === 'error' ? 'alert-danger' : 'alert-success'"
      role="status"
    >
      {{ message }}
      <button
        class="btn-close float-end"
        @click="message = ''"
        aria-label="Close"
      ></button>
    </div>

    <div class="row g-3 mb-4">
      <div class="col-6 col-xl-2" v-for="s in statCards" :key="s.label">
        <div class="stat-card h-100">
          <div class="stat-label">{{ s.label }}</div>
          <div class="stat-value">{{ counts[s.key] ?? 0 }}</div>
          <div class="stat-note">{{ s.note }}</div>
        </div>
      </div>
    </div>

    <ul class="nav nav-pills admin-tabs mb-4 flex-wrap gap-2">
      <li class="nav-item" v-for="t in tabs" :key="t.id">
        <button
          class="nav-link"
          :class="{ active: tab === t.id }"
          @click="tab = t.id"
        >
          {{ t.label }}
        </button>
      </li>
    </ul>

    <!-- OVERVIEW -->
    <section v-if="tab === 'overview'" class="row g-4">
      <div class="col-lg-7">
        <div class="card panel-card h-100">
          <div class="card-header bg-white d-flex justify-content-between">
            <h2 class="h5 mb-0">Examination status</h2>
            <button class="btn btn-sm btn-outline-secondary" @click="loadAll">
              Refresh
            </button>
          </div>
          <div class="table-responsive">
            <table class="table align-middle mb-0">
              <thead>
                <tr><th>Status</th><th>Count</th></tr>
              </thead>
              <tbody>
                <tr v-for="x in report.status || []" :key="x.examination_status">
                  <td>{{ x.examination_status }}</td>
                  <td>{{ x.count }}</td>
                </tr>
                <tr v-if="!report.status?.length">
                  <td colspan="2" class="text-secondary text-center py-3">
                    No examination data yet.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="col-lg-5">
        <div class="card panel-card h-100">
          <div class="card-header bg-white">
            <h2 class="h5 mb-0">Examiner workload</h2>
          </div>
          <div class="list-group list-group-flush">
            <div
              v-for="x in report.examiner_workload || []"
              :key="x.name"
              class="list-group-item d-flex justify-content-between gap-3"
            >
              <div>
                <div class="fw-semibold">{{ x.name }}</div>
                <div class="small text-secondary">
                  {{ x.examinations }} examinations
                </div>
              </div>
              <span class="badge text-bg-light align-self-center">
                {{ x.slots }} slots
              </span>
            </div>
            <div v-if="!report.examiner_workload?.length" class="p-3 text-secondary">
              No examiner workload available.
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- COURSES -->
    <section v-if="tab === 'courses'" class="row g-4">
      <div class="col-lg-4">
        <div class="card panel-card">
          <div class="card-header bg-white">
            <h2 class="h5 mb-0">
              {{ editingCourse ? 'Edit course' : 'Create course' }}
            </h2>
          </div>
          <div class="card-body">
            <form @submit.prevent="saveCourse">
              <label class="form-label">Course code</label>
              <input v-model.trim="course.course_code" class="form-control mb-3" required>

              <label class="form-label">Course name</label>
              <input v-model.trim="course.course_name" class="form-control mb-3" required>

              <label class="form-label">Description</label>
              <textarea v-model="course.description" class="form-control mb-3" rows="3"></textarea>

              <label class="form-label">Status</label>
              <select v-model="course.status" class="form-select mb-3">
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>

              <button class="btn btn-primary me-2">
                {{ editingCourse ? 'Save changes' : 'Create course' }}
              </button>
              <button
                v-if="editingCourse"
                type="button"
                class="btn btn-outline-secondary"
                @click="resetCourse"
              >
                Cancel
              </button>
            </form>
          </div>
        </div>
      </div>

      <div class="col-lg-8">
        <div class="card panel-card">
          <div class="card-header bg-white">
            <h2 class="h5 mb-0">All courses</h2>
          </div>
          <div class="table-responsive">
            <table class="table align-middle">
              <thead>
                <tr><th>Code</th><th>Course</th><th>Status</th><th>Actions</th></tr>
              </thead>
              <tbody>
                <tr v-for="c in courses" :key="c.id">
                  <td>{{ c.course_code }}</td>
                  <td>
                    <div class="fw-semibold">{{ c.course_name }}</div>
                    <div class="small text-secondary">{{ c.description }}</div>
                  </td>
                  <td>
                    <span
                      class="badge"
                      :class="c.status === 'active' ? 'text-bg-success' : 'text-bg-secondary'"
                    >{{ c.status }}</span>
                  </td>
                  <td class="text-nowrap">
                    <button class="btn btn-sm btn-outline-primary me-1" @click="editCourse(c)">Edit</button>
                    <button type="button" class="btn btn-sm btn-outline-danger" @click.stop.prevent="deleteCourse(c)">Delete</button>
                  </td>
                </tr>
                <tr v-if="!courses.length">
                  <td colspan="4" class="text-center text-secondary py-4">No courses created.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- EXAMINATIONS AND RUBRICS -->
    <section v-if="tab === 'exams'" class="row g-4">
      <div class="col-12">
        <div class="card panel-card">
          <div class="card-header bg-white">
            <h2 class="h5 mb-0">
              {{ editingExam ? 'Edit examination' : 'Create examination' }}
            </h2>
          </div>
          <div class="card-body">
            <form @submit.prevent="saveExam" class="row g-3">
              <div class="col-md-4">
                <label class="form-label">Course</label>
                <select v-model.number="exam.course_id" class="form-select" required>
                  <option disabled value="">Choose course</option>
                  <option v-for="c in courses" :key="c.id" :value="c.id">
                    {{ c.course_code }} — {{ c.course_name }}
                  </option>
                </select>
              </div>

              <div class="col-md-4">
                <label class="form-label">Examination name</label>
                <input v-model.trim="exam.examination_name" class="form-control" required>
              </div>

              <div class="col-md-4">
                <label class="form-label">Type</label>
                <select v-model="exam.examination_type" class="form-select">
                  <option>Viva</option>
                  <option>Practical</option>
                  <option>Project Demo</option>
                  <option>Assessment</option>
                </select>
              </div>

              <div class="col-md-3">
                <label class="form-label">Duration (minutes)</label>
                <input v-model.number="exam.duration" type="number" min="1" class="form-control" required>
              </div>

              <div class="col-md-3">
                <label class="form-label">Maximum marks</label>
                <input v-model.number="exam.maximum_marks" type="number" min="1" class="form-control" required>
              </div>

              <div class="col-md-3">
                <label class="form-label">Status / booking controls</label>
                <select v-model="exam.examination_status" class="form-select">
                  <option>Draft</option>
                  <option>Slot Creation</option>
                  <option>Booking Open</option>
                  <option>Closed</option>
                  <option>Completed</option>
                </select>
              </div>

              <div class="col-md-3">
                <label class="form-label">Instructions</label>
                <input v-model="exam.instructions" class="form-control">
              </div>

              <div class="col-md-6">
                <label class="form-label">Slot creation starts</label>
                <input v-model="exam.slot_creation_start" type="datetime-local" class="form-control">
              </div>

              <div class="col-md-6">
                <label class="form-label">Slot creation ends</label>
                <input v-model="exam.slot_creation_end" type="datetime-local" class="form-control">
              </div>

              <div class="col-md-6">
                <label class="form-label">Student booking starts</label>
                <input v-model="exam.slot_booking_start" type="datetime-local" class="form-control">
              </div>

              <div class="col-md-6">
                <label class="form-label">Student booking ends</label>
                <input v-model="exam.slot_booking_end" type="datetime-local" class="form-control">
              </div>

              <div class="col-12">
                <button class="btn btn-primary me-2">
                  {{ editingExam ? 'Save examination' : 'Create examination' }}
                </button>
                <button
                  v-if="editingExam"
                  type="button"
                  class="btn btn-outline-secondary"
                  @click="resetExam"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <div class="col-12">
        <div class="card panel-card">
          <div class="card-header bg-white d-flex flex-wrap justify-content-between gap-2">
            <h2 class="h5 mb-0">Examinations</h2>
            <input
              v-model="examSearch"
              class="form-control"
              style="max-width:300px"
              placeholder="Search examinations..."
            >
          </div>

          <div class="table-responsive">
            <table class="table align-middle">
              <thead>
                <tr>
                  <th>Examination</th>
                  <th>Course</th>
                  <th>Status</th>
                  <th>Timeline</th>
                  <th>Results</th>
                  <th>Actions</th>
                  <th>Assign examiner</th>
                </tr>
              </thead>

              <tbody>
                <tr v-for="e in filteredExams" :key="e.id">
                  <td>
                    <div class="fw-semibold">{{ e.examination_name }}</div>
                    <div class="small text-secondary">
                      {{ e.examination_type }} · {{ e.maximum_marks }} marks
                    </div>
                  </td>

                  <td>{{ e.course_code }} — {{ e.course_name }}</td>

                  <td>
                    <select
                      class="form-select form-select-sm"
                      :value="e.examination_status"
                      @change="setExamStatus(e, $event.target.value)"
                    >
                      <option>Draft</option>
                      <option>Slot Creation</option>
                      <option>Booking Open</option>
                      <option>Closed</option>
                      <option>Completed</option>
                    </select>
                  </td>

                  <td>
                    <div class="small">
                      Slots: {{ e.slot_creation_start || '—' }} → {{ e.slot_creation_end || '—' }}
                    </div>
                    <div class="small">
                      Booking: {{ e.slot_booking_start || '—' }} → {{ e.slot_booking_end || '—' }}
                    </div>
                  </td>

                  <td>
                    <button
                      v-if="!e.results_published"
                      type="button"
                      class="btn btn-sm btn-outline-success"
                      :disabled="loading"
                      @click.stop.prevent="handlePublish(e)"
                    >
                      Publish
                    </button>
                    <span v-else class="badge text-bg-success">Published</span>
                  </td>

                  <td class="text-nowrap">
                    <button type="button" class="btn btn-sm btn-outline-primary me-1" :disabled="loading" @click.stop.prevent="handleEdit(e)">Edit</button>
                    <button type="button" class="btn btn-sm btn-outline-secondary me-1" :disabled="loading" @click.stop.prevent="handleRubrics(e)">Rubrics</button>
                    <button type="button" class="btn btn-sm btn-outline-danger me-1" :disabled="loading" @click.stop.prevent="handleDeleteExam(e)">Delete/close</button>
                    <button
                      v-if="e.examination_status !== 'Slot Creation'"
                      type="button"
                      class="btn btn-sm btn-outline-success me-1"
                      :disabled="loading"
                      @click.stop.prevent="handleOpenSlotCreation(e)"
                    >
                      Open slot creation
                    </button>
                    <button
                      v-else
                      type="button"
                      class="btn btn-sm btn-outline-warning me-1"
                      :disabled="loading"
                      @click.stop.prevent="handleCloseSlotCreation(e)"
                    >
                      Close slot creation
                    </button>
                    <button
                      v-if="e.examination_status !== 'Booking Open'"
                      type="button"
                      class="btn btn-sm btn-outline-info"
                      :disabled="loading"
                      @click.stop.prevent="handleOpenBooking(e)"
                    >
                      Open booking
                    </button>
                    <button
                      v-else
                      type="button"
                      class="btn btn-sm btn-outline-secondary"
                      :disabled="loading"
                      @click.stop.prevent="handleCloseBooking(e)"
                    >
                      Close booking
                    </button>
                  </td>

                  <!-- EXAMINER ASSIGNMENT -->
                  <td style="min-width: 280px">
                    <div class="d-flex gap-2">
                      <select
                        v-model="examAssignment[e.id]"
                        class="form-select form-select-sm"
                      >
                        <option :value="null">Choose examiner</option>
                        <option
                          v-for="u in examiners"
                          :key="u.id"
                          :value="u.id"
                        >
                          {{ u.name }} ({{ u.department || 'No department' }})
                        </option>
                      </select>

                      <button
                        class="btn btn-sm btn-primary"
                        :disabled="!examAssignment[e.id] || assigningExam"
                        @click="assignExaminer(e)"
                      >
                        {{ assigningExam ? 'Assigning...' : 'Assign' }}
                      </button>
                    </div>
                  </td>
                </tr>

                <tr v-if="!filteredExams.length">
                  <td colspan="7" class="text-center text-secondary py-4">
                    No matching examinations.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- RUBRICS -->
      <div v-if="rubricExam" class="col-12">
        <div class="card panel-card">
          <div class="card-header bg-white d-flex justify-content-between">
            <h2 class="h5 mb-0">Rubrics · {{ rubricExam.examination_name }}</h2>
            <button class="btn btn-sm btn-outline-secondary" @click="rubricExam = null">Close</button>
          </div>

          <div class="card-body">
            <form @submit.prevent="createRubric" class="row g-2 mb-4">
              <div class="col-md-3">
                <input v-model.trim="rubric.criterion_name" class="form-control" placeholder="Criterion name" required>
              </div>
              <div class="col-md-2">
                <input v-model.number="rubric.maximum_marks" type="number" min="0" step="0.5" class="form-control" placeholder="Maximum marks" required>
              </div>
              <div class="col-md-2">
                <input v-model.number="rubric.weightage" type="number" min="0" step="0.1" class="form-control" placeholder="Weightage">
              </div>
              <div class="col-md-3">
                <input v-model="rubric.description" class="form-control" placeholder="Description">
              </div>
              <div class="col-md-2">
                <button class="btn btn-primary w-100">Add criterion</button>
              </div>
            </form>

            <div class="table-responsive">
              <table class="table">
                <thead>
                  <tr><th>Criterion</th><th>Marks</th><th>Weightage</th><th>Description</th><th></th></tr>
                </thead>
                <tbody>
                  <tr v-for="r in rubrics" :key="r.id">
                    <td>{{ r.criterion_name }}</td>
                    <td>{{ r.maximum_marks }}</td>
                    <td>{{ r.weightage }}</td>
                    <td>{{ r.description }}</td>
                    <td>
                      <button class="btn btn-sm btn-outline-danger" @click="deleteRubric(r)">Delete</button>
                    </td>
                  </tr>
                  <tr v-if="!rubrics.length">
                    <td colspan="5" class="text-secondary">No rubric criteria added.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- EXAM RUBRICS -->
    <section v-if="tab === 'rubrics'" class="card panel-card">
      <div class="card-header bg-white d-flex flex-wrap justify-content-between gap-2">
        <h2 class="h5 mb-0">Exam rubrics</h2>
        <select
          v-model.number="rubricExamId"
          class="form-select"
          style="max-width: 420px"
          @change="loadRubricsForSelectedExam"
        >
          <option :value="null">Select an examination</option>
          <option v-for="exam in exams" :key="exam.id" :value="exam.id">
            {{ exam.examination_name }} ({{ exam.course_code || exam.course_name || 'Course' }})
          </option>
        </select>
      </div>

      <div v-if="selectedRubricExam" class="card-body">
        <form @submit.prevent="createRubric" class="row g-2 mb-4">
          <div class="col-md-3">
            <input v-model.trim="rubric.criterion_name" class="form-control" placeholder="Criterion name" required>
          </div>
          <div class="col-md-2">
            <input v-model.number="rubric.maximum_marks" type="number" min="0" step="0.5" class="form-control" placeholder="Maximum marks" required>
          </div>
          <div class="col-md-2">
            <input v-model.number="rubric.weightage" type="number" min="0" step="0.1" class="form-control" placeholder="Weightage">
          </div>
          <div class="col-md-3">
            <input v-model="rubric.description" class="form-control" placeholder="Description">
          </div>
          <div class="col-md-2">
            <button class="btn btn-primary w-100">Add criterion</button>
          </div>
        </form>

        <div class="table-responsive">
          <table class="table align-middle mb-0">
            <thead>
              <tr><th>Criterion</th><th>Marks</th><th>Weightage</th><th>Description</th><th>Action</th></tr>
            </thead>
            <tbody>
              <tr v-for="r in rubrics" :key="r.id">
                <td>{{ r.criterion_name }}</td>
                <td>{{ r.maximum_marks }}</td>
                <td>{{ r.weightage }}</td>
                <td>{{ r.description || '—' }}</td>
                <td>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteRubric(r)">Delete</button>
                </td>
              </tr>
              <tr v-if="!rubrics.length">
                <td colspan="5" class="text-secondary text-center py-4">No rubric criteria added for this examination.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-else class="card-body text-secondary">
        Select an examination to add and manage rubrics.
      </div>
    </section>

    <!-- USERS AND EXAMINERS -->
    <section v-if="tab === 'users'" class="card panel-card">
      <div class="card-header bg-white d-flex flex-wrap justify-content-between gap-2">
        <h2 class="h5 mb-0">Students, examiners & accounts</h2>
        <div class="d-flex gap-2">
          <input v-model="userSearch" class="form-control" placeholder="Search name/email/department">
          <select v-model="userRole" class="form-select">
            <option value="all">All roles</option>
            <option value="student">Students</option>
            <option value="examiner">Examiners</option>
            <option value="admin">Admins</option>
          </select>
        </div>
      </div>

      <div class="card-body border-bottom">
        <form @submit.prevent="createExaminer" class="row g-2">
          <div class="col-md-3">
            <input v-model.trim="examiner.name" class="form-control" placeholder="Examiner name" required>
          </div>
          <div class="col-md-3">
            <input v-model.trim="examiner.email" type="email" class="form-control" placeholder="Examiner email" required>
          </div>
          <div class="col-md-2">
            <input v-model="examiner.password" type="password" minlength="8" class="form-control" placeholder="Temporary password" required>
          </div>
          <div class="col-md-2">
            <input v-model="examiner.department" class="form-control" placeholder="Department">
          </div>
          <div class="col-md-2">
            <button class="btn btn-primary w-100">Add examiner</button>
          </div>
        </form>
      </div>

      <div class="table-responsive">
        <table class="table align-middle">
          <thead>
            <tr><th>Name</th><th>Email</th><th>Role</th><th>Department</th><th>Status</th><th>Created</th><th>Account control</th></tr>
          </thead>
          <tbody>
            <tr v-for="u in filteredUsers" :key="u.id">
              <td>{{ u.name }}</td>
              <td>{{ u.email }}</td>
              <td><span class="badge text-bg-light">{{ u.role }}</span></td>
              <td>{{ u.department || '—' }}</td>
              <td>{{ u.account_status }}</td>
              <td>{{ u.created_at }}</td>
              <td>
                <button
                  v-if="u.role !== 'admin'"
                  class="btn btn-sm"
                  :class="u.account_status === 'active' ? 'btn-outline-danger' : 'btn-outline-success'"
                  @click="toggleUser(u)"
                >
                  {{ u.account_status === 'active' ? 'Disable' : 'Activate' }}
                </button>
                <span v-else class="small text-secondary">Protected</span>
              </td>
            </tr>
            <tr v-if="!filteredUsers.length">
              <td colspan="7" class="text-center text-secondary py-4">No matching accounts.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- EXAM SLOTS -->
    <section v-if="tab === 'slots'" class="card panel-card">
      <div class="card-header bg-white d-flex flex-wrap justify-content-between gap-2">
        <h2 class="h5 mb-0">All examiner slots</h2>
        <div class="d-flex gap-2">
          <input v-model="slotSearch" class="form-control" placeholder="Search exam, examiner, date">
          <select v-model="slotStatus" class="form-select">
            <option value="all">All statuses</option>
            <option>Available</option>
            <option>Full</option>
            <option>Cancelled</option>
            <option>Completed</option>
          </select>
        </div>
      </div>

      <div class="table-responsive">
        <table class="table align-middle">
          <thead>
            <tr><th>ID</th><th>Examination</th><th>Examiner</th><th>Date / time</th><th>Capacity</th><th>Status</th><th>Reassign examiner</th></tr>
          </thead>
          <tbody>
            <tr v-for="s in filteredSlots" :key="s.id">
              <td>#{{ s.id }}</td>
              <td>{{ s.examination_name }}</td>
              <td>{{ s.examiner_name }}</td>
              <td>{{ s.exam_date }} · {{ s.start_time }}–{{ s.end_time }}</td>
              <td>{{ s.maximum_capacity - s.available_seats }} booked / {{ s.maximum_capacity }} total</td>
              <td>
                <span
                  class="badge"
                  :class="s.status === 'Available' ? 'text-bg-success' : s.status === 'Full' ? 'text-bg-warning' : 'text-bg-secondary'"
                >{{ s.status }}</span>
              </td>
              <td>
                <div class="d-flex gap-1">
                  <select v-model.number="slotReassign[s.id]" class="form-select form-select-sm">
                    <option disabled value="">Choose examiner</option>
                    <option v-for="u in examiners" :key="u.id" :value="u.id">{{ u.name }}</option>
                  </select>
                  <button class="btn btn-sm btn-outline-primary" @click="reassignExaminer(s)">Assign</button>
                </div>
              </td>
            </tr>
            <tr v-if="!filteredSlots.length">
              <td colspan="7" class="text-center text-secondary py-4">No slots found.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- BOOKINGS -->
    <section v-if="tab === 'bookings'" class="card panel-card">
      <div class="card-header bg-white d-flex flex-wrap justify-content-between gap-2">
        <h2 class="h5 mb-0">All bookings & rescheduling</h2>
        <input
          v-model="bookingSearch"
          class="form-control"
          style="max-width:340px"
          placeholder="Search student, exam, examiner, status"
        >
      </div>

      <div class="table-responsive">
        <table class="table align-middle">
          <thead>
            <tr><th>Booking</th><th>Student</th><th>Examination</th><th>Current slot</th><th>Examiner</th><th>Status</th><th>Move to slot</th><th>Actions</th></tr>
          </thead>
          <tbody>
            <tr v-for="b in filteredBookings" :key="b.id">
              <td>#{{ b.id }}<div class="small text-secondary">{{ b.booking_date }}</div></td>
              <td>{{ b.student_name || ('Student #' + b.student_id) }}</td>
              <td>{{ b.examination_name || '—' }}</td>
              <td>{{ b.exam_date || '—' }} {{ b.start_time || '' }}</td>
              <td>{{ b.examiner_name || '—' }}</td>
              <td>{{ b.status }}</td>
              <td>
                <select
                  v-model.number="bookingMove[b.id]"
                  class="form-select form-select-sm"
                  :disabled="b.status !== 'Booked' || !getAvailableMoveSlots(b).length"
                  :title="b.status === 'Booked'
                    ? (getAvailableMoveSlots(b).length ? 'Choose a destination slot for this booking' : 'No eligible destination slots are available for this booked exam')
                    : 'Only active Booked bookings can be rescheduled'"
                >
                  <option :value="null" disabled>
                    {{ b.status === 'Booked'
                      ? (getAvailableMoveSlots(b).length ? 'Choose available slot' : 'No available slots')
                      : 'Reschedule unavailable' }}
                  </option>
                  <option
                    v-for="s in getAvailableMoveSlots(b)"
                    :key="s.id"
                    :value="s.id"
                  >
                    {{ s.examination_name }} · {{ s.exam_date }} {{ s.start_time }} · {{ s.examiner_name }}
                  </option>
                </select>
              </td>
              <td class="text-nowrap">
                <button
                  class="btn btn-sm btn-primary me-1"
                  :disabled="b.status !== 'Booked' || !bookingMove[b.id]"
                  :title="b.status === 'Booked'
                    ? (bookingMove[b.id] ? 'Reschedule to the selected slot' : 'Select a destination slot first')
                    : 'Only active Booked bookings can be rescheduled'"
                  @click="reschedule(b)"
                >Reschedule</button>
                <button
                  v-if="b.status === 'Booked'"
                  class="btn btn-sm btn-outline-danger"
                  @click="cancelBooking(b)"
                >Cancel</button>
              </td>
            </tr>
            <tr v-if="!filteredBookings.length">
              <td colspan="8" class="text-center text-secondary py-4">No matching bookings.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- REPORTS -->
    <section v-if="tab === 'reports'" class="row g-4">
      <div class="col-lg-6">
        <div class="card panel-card">
          <div class="card-header bg-white">
            <h2 class="h5 mb-0">Examinations by type</h2>
          </div>
          <div class="list-group list-group-flush">
            <div
              v-for="x in report.types || []"
              :key="x.examination_type"
              class="list-group-item d-flex justify-content-between"
            >
              <span>{{ x.examination_type }}</span>
              <strong>{{ x.count }}</strong>
            </div>
            <div v-if="!report.types?.length" class="p-3 text-secondary">No report data yet.</div>
          </div>
        </div>
      </div>

      <div class="col-lg-6">
        <div class="card panel-card">
          <div class="card-header bg-white">
            <h2 class="h5 mb-0">Operational summary</h2>
          </div>
          <div class="card-body">
            <div class="d-flex justify-content-between py-2 border-bottom">
              <span>Pending evaluations</span>
              <strong>{{ counts.pending_evaluations ?? 0 }}</strong>
            </div>
            <div class="d-flex justify-content-between py-2">
              <span>Examinations with published results</span>
              <strong>{{ counts.published_results ?? 0 }}</strong>
            </div>
            <p class="small text-secondary mt-3 mb-0">
              Counts are retrieved from the Flask API and SQLite database.
            </p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { api } from '../services/api'

const blankExam = () => ({
  course_id: '',
  examination_name: '',
  examination_type: 'Viva',
  description: '',
  duration: 15,
  maximum_marks: 100,
  examination_status: 'Draft',
  instructions: '',
  slot_creation_start: '',
  slot_creation_end: '',
  slot_booking_start: '',
  slot_booking_end: ''
})

export default {
  data: () => ({
    tab: 'overview',
    tabs: [
      { id: 'overview', label: 'Overview' },
      { id: 'courses', label: 'Courses' },
      { id: 'exams', label: 'Examinations' },
      { id: 'rubrics', label: 'Exam rubrics' },
      { id: 'users', label: 'Users & examiners' },
      { id: 'slots', label: 'Exam slots' },
      { id: 'bookings', label: 'Bookings' },
      { id: 'reports', label: 'Reports' }
    ],
    statCards: [
      { key: 'courses', label: 'Courses', note: 'Course catalogue' },
      { key: 'examinations', label: 'Examinations', note: 'All exams' },
      { key: 'students', label: 'Students', note: 'Registered learners' },
      { key: 'examiners', label: 'Examiners', note: 'Faculty accounts' },
      { key: 'slots', label: 'Exam slots', note: 'All schedules' },
      { key: 'bookings', label: 'Bookings', note: 'All records' }
    ],
    counts: {},
    report: {},
    courses: [],
    exams: [],
    users: [],
    slots: [],
    bookings: [],
    rubrics: [],
    message: '',
    messageType: 'success',
    loading: false,
    assigningExam: false,
    course: {
      course_code: '',
      course_name: '',
      description: '',
      status: 'active'
    },
    exam: blankExam(),
    examiner: {
      name: '',
      email: '',
      password: '',
      department: '',
      contact_details: ''
    },
    rubric: {
      criterion_name: '',
      maximum_marks: 0,
      weightage: 1,
      description: ''
    },
    editingCourse: null,
    editingExam: null,
    rubricExam: null,
    rubricExamId: null,
    examSearch: '',
    userSearch: '',
    userRole: 'all',
    slotSearch: '',
    slotStatus: 'all',
    bookingSearch: '',
    slotReassign: {},
    bookingMove: {},
    examAssignment: {}
  }),

  computed: {
    selectedRubricExam() {
      return this.exams.find(exam => exam.id === this.rubricExamId) || null
    },

    filteredExams() {
      const q = this.examSearch.toLowerCase()
      return this.exams.filter(e =>
        [
          e.examination_name,
          e.course_name,
          e.course_code,
          e.examination_type,
          e.examination_status
        ].some(v => String(v || '').toLowerCase().includes(q))
      )
    },

    filteredUsers() {
      const q = this.userSearch.toLowerCase()
      return this.users.filter(u =>
        (this.userRole === 'all' || u.role === this.userRole) &&
        [u.name, u.email, u.department, u.role, u.account_status]
          .some(v => String(v || '').toLowerCase().includes(q))
      )
    },

    examiners() {
      return this.users.filter(
        u => u.role === 'examiner' && u.account_status === 'active'
      )
    },

    filteredSlots() {
      const q = this.slotSearch.toLowerCase()
      return this.slots.filter(s =>
        (this.slotStatus === 'all' || s.status === this.slotStatus) &&
        [s.examination_name, s.examiner_name, s.exam_date, s.status]
          .some(v => String(v || '').toLowerCase().includes(q))
      )
    },

    filteredBookings() {
      const q = this.bookingSearch.toLowerCase()
      return this.bookings.filter(b =>
        [
          b.student_name,
          b.examination_name,
          b.examiner_name,
          b.status,
          b.exam_date,
          b.id
        ].some(v => String(v || '').toLowerCase().includes(q))
      )
    }
  },

  async mounted() {
    await this.loadAll()
  },

  methods: {
    notify(msg, type = 'success') {
      this.message = msg
      this.messageType = type
    },

    async safe(promise, fallback) {
      try {
        return (await promise).data
      } catch (e) {
        throw new Error(e.response?.data?.error || fallback)
      }
    },

    async assignExaminer(exam) {
      const examinerId = this.examAssignment[exam.id]

      if (!examinerId) {
        this.notify('Please select an examiner first.', 'error')
        return
      }

      this.assigningExam = true

      try {
        // This URL must match the assignment route registered in your Flask backend.
        const response = await api.post(
          `/examinations/${exam.id}/assign-examiner`,
          { examiner_id: Number(examinerId) }
        )

        this.notify(
          response.data.message || 'Examiner assigned successfully.'
        )

        this.examAssignment[exam.id] = null
        await this.loadAll()
      } catch (error) {
        this.notify(
          error.response?.data?.error ||
          'Examiner assignment failed. Check the backend endpoint.',
          'error'
        )
      } finally {
        this.assigningExam = false
      }
    },

    getAvailableMoveSlots(b) {
      if (!b || b.status !== 'Booked' || !b.examination_id) return []
      return this.slots.filter(
        x =>
          x.id !== b.slot_id &&
          x.examination_id === b.examination_id &&
          x.status in ['Available', 'Full'] &&
          x.available_seats > 0
      )
    },

    async loadAll() {
      this.loading = true

      try {
        const jobs = await Promise.allSettled([
          api.get('/admin/dashboard'),
          api.get('/courses'),
          api.get('/examinations'),
          api.get('/admin/users'),
          api.get('/slots'),
          api.get('/admin/bookings'),
          api.get('/reports/summary')
        ])

        const val = i =>
          jobs[i].status === 'fulfilled' ? jobs[i].value.data : null

        this.counts = val(0)?.counts || {}
        this.courses = val(1)?.items || []
        this.exams = val(2)?.items || []
        this.users = val(3)?.items || []
        this.slots = val(4)?.items || []
        this.bookings = val(5)?.items || []
        this.report = val(6) || {}

        const errors = jobs.filter(x => x.status === 'rejected')

        if (errors.length) {
          this.notify(
            'Some panels could not load. Confirm backend is running and the admin session is active.',
            'error'
          )
        }
      } catch (e) {
        this.notify(e.message || 'Unable to load dashboard', 'error')
      } finally {
        this.loading = false
      }
    },

    resetCourse() {
      this.editingCourse = null
      this.course = {
        course_code: '',
        course_name: '',
        description: '',
        status: 'active'
      }
    },

    editCourse(c) {
      this.editingCourse = c.id
      this.course = {
        course_code: c.course_code,
        course_name: c.course_name,
        description: c.description || '',
        status: c.status || 'active'
      }
      this.tab = 'courses'
    },

    async saveCourse() {
      try {
        if (this.editingCourse) {
          await api.put(`/courses/${this.editingCourse}`, this.course)
        } else {
          await api.post('/courses', this.course)
        }

        this.notify(this.editingCourse ? 'Course updated' : 'Course created')
        this.resetCourse()
        await this.loadAll()
      } catch (e) {
        this.notify(e.response?.data?.error || 'Course save failed', 'error')
      }
    },

    async deleteCourse(c) {
      if (!confirm(`Delete ${c.course_code} — ${c.course_name}?`)) return

      try {
        const r = await api.delete(`/courses/${c.id}`)
        this.notify(r.data.message || 'Course deleted')
        await this.loadAll()
      } catch (e) {
        this.notify(e.response?.data?.error || 'Course delete failed', 'error')
      }
    },

    resetExam() {
      this.editingExam = null
      this.exam = blankExam()
    },

    editExam(e) {
      this.editingExam = e.id
      this.exam = {
        ...blankExam(),
        ...e,
        slot_creation_start: this.toLocal(e.slot_creation_start),
        slot_creation_end: this.toLocal(e.slot_creation_end),
        slot_booking_start: this.toLocal(e.slot_booking_start),
        slot_booking_end: this.toLocal(e.slot_booking_end)
      }
      this.tab = 'exams'
    },

    toLocal(v) {
      return v ? String(v).slice(0, 16) : ''
    },

    async saveExam() {
      try {
        const payload = {
          ...this.exam,
          slot_creation_start: this.exam.slot_creation_start || null,
          slot_creation_end: this.exam.slot_creation_end || null,
          slot_booking_start: this.exam.slot_booking_start || null,
          slot_booking_end: this.exam.slot_booking_end || null
        }

        if (this.editingExam) {
          await api.put(`/examinations/${this.editingExam}`, payload)
        } else {
          await api.post('/examinations', payload)
        }

        this.notify(this.editingExam ? 'Examination updated' : 'Examination created')
        this.resetExam()
        await this.loadAll()
      } catch (e) {
        this.notify(e.response?.data?.error || 'Examination save failed', 'error')
      }
    },

    async setExamStatus(e, status) {
      try {
        await api.put(`/examinations/${e.id}`, {
          ...e,
          examination_status: status
        })
        this.notify(`Status changed to ${status}`)
        await this.loadAll()
      } catch (x) {
        this.notify(x.response?.data?.error || 'Could not change status', 'error')
      }
    },

    handlePublish(e) {
      return this.publish(e)
    },

    handleEdit(e) {
      return this.editExam(e)
    },

    handleRubrics(e) {
      return this.openRubrics(e)
    },

    handleDeleteExam(e) {
      return this.deleteExam(e)
    },

    handleOpenSlotCreation(exam) {
      return this.openExaminerSlotCreation(exam)
    },

    handleCloseSlotCreation(exam) {
      return this.closeExaminerSlotCreation(exam)
    },

    handleOpenBooking(exam) {
      return this.openStudentBooking(exam)
    },

    handleCloseBooking(exam) {
      return this.closeStudentBooking(exam)
    },

    async openExaminerSlotCreation(exam) {
      if (!confirm(`Open slot creation for "${exam.examination_name}"?`)) return
      await this.setExamStatus(exam, 'Slot Creation')
    },

    async closeExaminerSlotCreation(exam) {
      if (!confirm(`Close slot creation for "${exam.examination_name}"?`)) return
      await this.setExamStatus(exam, 'Closed')
    },

    async openStudentBooking(exam) {
      if (!confirm(`Open student booking for "${exam.examination_name}"?`)) return
      await this.setExamStatus(exam, 'Booking Open')
    },

    async closeStudentBooking(exam) {
      if (!confirm(`Close student booking for "${exam.examination_name}"?`)) return
      await this.setExamStatus(exam, 'Closed')
    },

    async deleteExam(e) {
      if (!confirm(`Delete or close "${e.examination_name}"?`)) return

      try {
        const r = await api.delete(`/examinations/${e.id}`)
        this.notify(r.data.message || 'Examination removed/closed')
        await this.loadAll()
      } catch (x) {
        this.notify(x.response?.data?.error || 'Could not delete examination', 'error')
      }
    },

    async publish(e) {
      if (!confirm(`Publish results for ${e.examination_name}? Students will be able to view published results.`)) return

      try {
        await api.post(`/admin/examinations/${e.id}/publish`)
        this.notify('Results published')
        await this.loadAll()
      } catch (x) {
        this.notify(x.response?.data?.error || 'Could not publish results', 'error')
      }
    },

    async toggleUser(u) {
      const next = u.account_status === 'active' ? 'disabled' : 'active'

      if (!confirm(`${next} account for ${u.name}?`)) return

      try {
        await api.patch(`/admin/users/${u.id}/status`, {
          account_status: next
        })
        this.notify(`Account ${next}`)
        await this.loadAll()
      } catch (e) {
        this.notify(e.response?.data?.error || 'Could not update account status', 'error')
      }
    },

    async createExaminer() {
      try {
        await api.post('/admin/examiners', this.examiner)
        this.notify('Examiner account created')

        this.examiner = {
          name: '',
          email: '',
          password: '',
          department: '',
          contact_details: ''
        }

        await this.loadAll()
      } catch (e) {
        this.notify(e.response?.data?.error || 'Examiner creation failed', 'error')
      }
    },

    async loadRubricsForSelectedExam() {
      const exam = this.selectedRubricExam

      if (!exam) {
        this.rubrics = []
        this.rubricExam = null
        return
      }

      this.rubricExam = exam
      this.rubric = {
        criterion_name: '',
        maximum_marks: 0,
        weightage: 1,
        description: ''
      }

      try {
        this.rubrics = (await api.get(`/examinations/${exam.id}/rubrics`)).data.items || []
      } catch (x) {
        this.notify(x.response?.data?.error || 'Could not load rubrics', 'error')
      }
    },

    async openRubrics(e) {
      this.rubricExam = e
      this.rubricExamId = e.id
      this.tab = 'rubrics'
      await this.loadRubricsForSelectedExam()
    },

    async createRubric() {
      const exam = this.selectedRubricExam || this.rubricExam

      if (!exam) {
        this.notify('Select an examination before adding rubrics.', 'error')
        return
      }

      try {
        await api.post(`/examinations/${exam.id}/rubrics`, this.rubric)
        this.notify('Rubric criterion added')

        this.rubric = {
          criterion_name: '',
          maximum_marks: 0,
          weightage: 1,
          description: ''
        }

        await this.loadRubricsForSelectedExam()
      } catch (e) {
        this.notify(e.response?.data?.error || 'Could not add rubric', 'error')
      }
    },

    async deleteRubric(r) {
      if (!confirm(`Delete rubric "${r.criterion_name}"?`)) return

      try {
        await api.delete(`/examinations/rubrics/${r.id}`)
        this.notify('Rubric deleted')
        await this.loadRubricsForSelectedExam()
      } catch (e) {
        this.notify(e.response?.data?.error || 'Rubric delete failed', 'error')
      }
    },

    async reassignExaminer(s) {
      const id = this.slotReassign[s.id]
      if (!id) return

      try {
        await api.post(`/admin/slots/${s.id}/reassign-examiner`, {
          examiner_id: id
        })
        this.notify('Examiner reassigned to slot')
        await this.loadAll()
      } catch (e) {
        this.notify(e.response?.data?.error || 'Could not reassign examiner', 'error')
      }
    },

    async reschedule(b) {
      if (b.status !== 'Booked') {
        this.notify('Only active Booked bookings can be rescheduled.', 'error')
        return
      }

      const id = this.bookingMove[b.id]
      if (!id) {
        this.notify('Select a valid destination slot before rescheduling.', 'error')
        return
      }

      if (!confirm(`Reschedule booking #${b.id} to slot #${id}?`)) return

      try {
        await api.post(`/admin/bookings/${b.id}/reschedule`, {
          slot_id: id
        })
        this.notify('Booking rescheduled')
        await this.loadAll()
      } catch (e) {
        this.notify(e.response?.data?.error || 'Could not reschedule booking', 'error')
      }
    },

    async cancelBooking(b) {
      if (!confirm(`Cancel booking #${b.id}?`)) return

      try {
        await api.post(`/bookings/${b.id}/cancel`)
        this.notify('Booking cancelled')
        await this.loadAll()
      } catch (e) {
        this.notify(e.response?.data?.error || 'Could not cancel booking', 'error')
      }
    }
  }
}
</script>

<style scoped>
.admin-page {
  position: relative;
  min-height: 78vh;
  padding-left: 244px;
  color: #172033;
}

.admin-tabs {
  position: absolute;
  left: 0;
  top: 0;
  width: 220px;
  margin: 0 !important;
  padding: 14px 10px;
  background: #fff;
  border: 1px solid #e5eaf2;
  border-radius: 18px;
  box-shadow: 0 8px 26px rgba(23, 35, 60, 0.06);
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 6px !important;
}

.admin-tabs::before {
  content: "ADMIN WORKSPACE";
  display: block;
  padding: 8px 12px 12px;
  color: #8792a6;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.14em;
}

.admin-tabs .nav-item {
  width: 100%;
}

.admin-tabs .nav-link {
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: #43516a;
  padding: 0.78rem 0.85rem;
  font-size: 0.9rem;
  font-weight: 600;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.admin-tabs .nav-link:hover {
  background: #f4f6ff;
  color: #2447bd;
}

.admin-tabs .nav-link.active {
  background: #edf1ff;
  color: #2447bd;
  border-color: #dce4ff;
  box-shadow: inset 3px 0 #3759d7;
}

.admin-page .stat-card {
  height: 100%;
  padding: 18px;
  background: #fff;
  border: 1px solid #e7ebf3;
  border-radius: 16px;
  box-shadow: 0 5px 18px rgba(23, 35, 60, 0.04);
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.admin-page .stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(23, 35, 60, 0.08);
}

.admin-page .stat-label {
  color: #64748b;
  font-size: 0.83rem;
  font-weight: 600;
}

.admin-page .stat-value {
  margin: 8px 0;
  color: #1e3a8a;
  font-size: 1.8rem;
  font-weight: 800;
}

.admin-page .stat-note {
  color: #94a3b8;
  font-size: 0.78rem;
}

.admin-page .page-title {
  margin: 4px 0 8px;
  color: #172033;
  font-size: clamp(1.6rem, 2.5vw, 2.2rem);
  font-weight: 800;
  letter-spacing: -0.04em;
}

.admin-page .eyebrow {
  color: #3759d7;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.15em;
}

.admin-page .panel-card {
  overflow: hidden;
  background: #fff;
  border: 1px solid #e7ebf3;
  border-radius: 16px;
  box-shadow: 0 5px 18px rgba(23, 35, 60, 0.04);
}

.admin-page .card-header {
  padding: 1rem 1.1rem;
  border-bottom: 1px solid #edf0f5;
}

.admin-page .card-body {
  padding: 1.1rem;
}

.admin-page .table {
  margin-bottom: 0;
}

.admin-page .table th {
  color: #64748b;
  font-size: 0.76rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
  background: #f8fafc;
}

.admin-page .table td {
  font-size: 0.9rem;
  vertical-align: middle;
}

.admin-page .table tbody tr:hover > * {
  background-color: #f8faff;
}

.admin-page .form-control,
.admin-page .form-select {
  min-width: 0;
  border-color: #dbe2ed;
  border-radius: 9px;
}

.admin-page .form-control:focus,
.admin-page .form-select:focus {
  border-color: #7c96f8;
  box-shadow: 0 0 0 3px rgba(55, 89, 215, 0.12);
}

.admin-page .btn {
  border-radius: 9px;
  font-weight: 600;
}

@media (max-width: 991.98px) {
  .admin-page {
    padding-left: 0;
  }

  .admin-tabs {
    position: static;
    width: 100%;
    margin-bottom: 1.25rem !important;
    flex-direction: row;
    flex-wrap: wrap;
  }

  .admin-tabs::before {
    width: 100%;
    padding-bottom: 4px;
  }

  .admin-tabs .nav-item {
    width: auto;
  }

  .admin-tabs .nav-link {
    width: auto;
    text-align: center;
  }
}

@media (max-width: 575.98px) {
  .admin-tabs {
    padding: 10px;
  }

  .admin-tabs .nav-link {
    padding: 0.58rem 0.7rem;
    font-size: 0.82rem;
  }

  .admin-page .card-body {
    padding: 0.9rem;
  }

  .admin-page .stat-card {
    padding: 13px;
  }

  .admin-page .stat-value {
    font-size: 1.45rem;
  }
}
</style>