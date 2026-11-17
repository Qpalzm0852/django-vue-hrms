from django.urls import path, include
from rest_framework.routers import DefaultRouter
from Model.views import (
    DepartmentViewSet,
    JobPositionViewSet,
    EmployeeProfileViewSet,
    AttendanceRecordViewSet,
    LeaveRequestViewSet,
    PayrollViewSet,
    PerformanceRecordViewSet,
    TrainingViewSet,
    AnnouncementViewSet,
    OvertimeRequestViewSet,
    OperationLogViewSet,
    RecruitmentRequirementViewSet,
    ResumeViewSet,
    InterviewViewSet,
    OfferViewSet,
    overview_statistics,
    employee_overview_statistics,
    statistics_dashboard,
    import_employees,
    import_attendance,
)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'positions', JobPositionViewSet, basename='position')
router.register(r'employees', EmployeeProfileViewSet, basename='employee')
router.register(r'attendance', AttendanceRecordViewSet, basename='attendance')
router.register(r'leave', LeaveRequestViewSet, basename='leave')
router.register(r'payroll', PayrollViewSet, basename='payroll')
router.register(r'performance', PerformanceRecordViewSet, basename='performance')
router.register(r'training', TrainingViewSet, basename='training')
router.register(r'announcement', AnnouncementViewSet, basename='announcement')
router.register(r'overtime', OvertimeRequestViewSet, basename='overtime')
router.register(r'operation-logs', OperationLogViewSet, basename='operation-log')
router.register(r'recruitment-requirements', RecruitmentRequirementViewSet, basename='recruitment-requirement')
router.register(r'resumes', ResumeViewSet, basename='resume')
router.register(r'interviews', InterviewViewSet, basename='interview')
router.register(r'offers', OfferViewSet, basename='offer')

urlpatterns = [
    path('', include(router.urls)),
    path('statistics/overview/', overview_statistics, name='overview-statistics'),
    path('statistics/employee-overview/', employee_overview_statistics, name='employee-overview-statistics'),
    path('statistics/dashboard/', statistics_dashboard, name='statistics-dashboard'),
    path('import/employees/', import_employees, name='import-employees'),
    path('import/attendance/', import_attendance, name='import-attendance'),
]

