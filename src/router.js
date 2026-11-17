import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

const Login = () => import('./components/Login.vue')

const HomeAdmin = () => import('./components/admin/Home.vue')
const WelcomeAdmin = () => import('./components/admin/Welcome.vue')
const Admins = () => import('./components/admin/Admins.vue')
const Students = () => import('./components/admin/Students.vue')
const Departments = () => import('./components/admin/Departments.vue')
const Positions = () => import('./components/admin/Positions.vue')
const Selections = () => import('./components/admin/Selections.vue')
const Scores = () => import('./components/admin/Scores.vue')
const ScoresAnalysis = () => import('./components/admin/ScoresAnalysis.vue')
const Performance = () => import('./components/admin/Performance.vue')
const Training = () => import('./components/admin/Training.vue')
const Announcement = () => import('./components/admin/Announcement.vue')
const Overtime = () => import('./components/admin/Overtime.vue')
const Dashboard = () => import('./components/admin/Dashboard.vue')
const OperationLogs = () => import('./components/admin/OperationLogs.vue')
const Recruitment = () => import('./components/admin/Recruitment.vue')

const HomeEmployee = () => import('./components/employee/Home.vue')
const WelcomeEmployee = () => import('./components/employee/Welcome.vue')
const PayrollEmployee = () => import('./components/employee/Payroll.vue')
const AttendanceEmployee = () => import('./components/employee/Attendance.vue')
const LeaveEmployee = () => import('./components/employee/Leave.vue')
const OvertimeEmployee = () => import('./components/employee/Overtime.vue')
const PerformanceEmployee = () => import('./components/employee/Performance.vue')
const TrainingEmployee = () => import('./components/employee/Training.vue')
const ProfileEmployee = () => import('./components/employee/Profile.vue')
const AnnouncementEmployee = () => import('./components/employee/Announcement.vue')

const router = new Router({
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', component: Login },

    { path: '/admin', redirect: '/admin/home' },
    {
      path: '/admin/home',
      component: HomeAdmin,
      redirect: '/admin/welcome',
      children: [
        { path: '/admin/welcome', component: WelcomeAdmin },
        { path: '/admin/admins', component: Admins },
        { path: '/admin/students', component: Students },
        { path: '/admin/departments', component: Departments },
        { path: '/admin/positions', component: Positions },
        { path: '/admin/selections', component: Selections },
        { path: '/admin/scores', component: Scores },
        { path: '/admin/scoresAnalysis', component: ScoresAnalysis },
        { path: '/admin/performance', component: Performance },
        { path: '/admin/training', component: Training },
        { path: '/admin/announcement', component: Announcement },
        { path: '/admin/overtime', component: Overtime },
        { path: '/admin/dashboard', component: Dashboard },
        { path: '/admin/operationlogs', component: OperationLogs },
        { path: '/admin/recruitment', component: Recruitment },
      ],
    },

    {
      path: '/employee/home',
      component: HomeEmployee,
      redirect: '/employee/welcome',
      children: [
        { path: '/employee/welcome', component: WelcomeEmployee },
        { path: '/employee/payroll', component: PayrollEmployee },
        { path: '/employee/attendance', component: AttendanceEmployee },
        { path: '/employee/leave', component: LeaveEmployee },
        { path: '/employee/overtime', component: OvertimeEmployee },
        { path: '/employee/performance', component: PerformanceEmployee },
        { path: '/employee/training', component: TrainingEmployee },
        { path: '/employee/profile', component: ProfileEmployee },
        { path: '/employee/announcement', component: AnnouncementEmployee },
      ],
    },
  ],
})

router.beforeEach((to, from, next) => {
  if (to.path === '/login') {
    return next()
  }

  const deletedRoutes = [
    '/admin/colleges',
    '/admin/teachers',
    '/admin/courses',
    '/admin/opens',
    '/admin/addSelection',
    '/student',
    '/teacher',
  ]

  if (deletedRoutes.some((route) => to.path.startsWith(route))) {
    if (to.path.startsWith('/admin/')) {
      return next('/admin/welcome')
    }
    return next('/login')
  }

  const tokenStr = window.sessionStorage.getItem('token')
  if (!tokenStr) {
    return next('/login')
  }

  return next()
})

export default router
