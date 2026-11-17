# MyWeb/Model/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# 角色枚举
ROLE_CHOICES = (
    ("ADMIN", "Admin"),
    ("HR", "HR"),
    ("MANAGER", "Manager"),
    ("STAFF", "Staff"),
)

STATUS_CHOICES = (
    ("ONBOARD", "在职"),
    ("PROBATION", "试用"),
    ("LEAVE", "离职"),
    ("SUSPEND", "停薪留职"),
)

REQ_STATUS = (
    ("PENDING", "待审批"),
    ("APPROVED", "已通过"),
    ("REJECTED", "已拒绝"),
)

PAY_STATUS = (
    ("DRAFT", "草稿"),
    ("CONFIRMED", "已确认"),
)

# 自定义用户
class UserManager(BaseUserManager):
    def create_user(self, user_id, name, password=None, role="STAFF", **extra):
        if not user_id:
            raise ValueError("user_id required")
        user = self.model(user_id=user_id, name=name, role=role, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id, name, password=None, **extra):
        extra.setdefault("is_admin", True)
        extra.setdefault("is_active", True)
        extra.setdefault("role", "ADMIN")
        return self.create_user(user_id, name, password, **extra)
    
    def get_by_natural_key(self, user_id):
        """用于认证时查找用户"""
        return self.get(user_id=user_id)

class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=50)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="STAFF")
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = "user_id"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        db_table = "user"

    def __str__(self):
        return f"{self.user_id}({self.name})"

    @property
    def is_staff(self):
        return self.is_admin

    @property
    def is_superuser(self):
        """Django JWT 认证需要这个属性"""
        return self.is_admin

# 部门
class Department(models.Model):
    name = models.CharField(max_length=100)
    manager = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_departments")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "department"

    def __str__(self):
        return self.name

# 岗位
class JobPosition(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="positions")
    level_code = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)  # 技术/职能/管理
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "job_position"

    def __str__(self):
        return self.name

# 员工档案
class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name="profile")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="employees")
    position = models.ForeignKey(JobPosition, null=True, blank=True, on_delete=models.SET_NULL, related_name="employees")
    hire_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ONBOARD")
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="基本工资")
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    id_no = models.CharField(max_length=30, blank=True, null=True)
    education = models.CharField(max_length=50, blank=True, null=True)
    contract_end = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "employee_profile"

    def __str__(self):
        return f"{self.user_id}-{self.user.name}"

# 考勤
class AttendanceRecord(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attendance_records")
    work_date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    work_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    abnormal = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attendance_record"
        unique_together = ("employee", "work_date")

# 请假
class LeaveRequest(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="leave_requests")
    type = models.CharField(max_length=30)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reason = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=10, choices=REQ_STATUS, default="PENDING")
    approver = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="leave_approvals")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "leave_request"

# 加班
class OvertimeRequest(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="overtime_requests")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reason = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=10, choices=REQ_STATUS, default="PENDING")
    approver = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="overtime_approvals")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "overtime_request"

# 薪酬
class Payroll(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payrolls")
    period = models.CharField(max_length=7)  # YYYY-MM
    base_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    social_security = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    housing_fund = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=PAY_STATUS, default="DRAFT")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payroll"
        unique_together = ("employee", "period")

# 绩效
class PerformanceRecord(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="performance_records")
    period = models.CharField(max_length=7)  # YYYY-MM 或 YYYY-Qn
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dimension = models.CharField(max_length=50, null=True, blank=True)
    comment = models.CharField(max_length=255, null=True, blank=True)
    evaluator = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="performance_evaluations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "performance_record"
        unique_together = ("employee", "period")

# 培训
class Training(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    participants_scope = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "training"

# 公告
class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(null=True, blank=True)
    level = models.CharField(max_length=50, null=True, blank=True)
    publisher = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="announcements")
    publish_time = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "announcement"

# 操作日志
ACTION_TYPE_CHOICES = (
    ('CREATE', '创建'),
    ('UPDATE', '更新'),
    ('DELETE', '删除'),
    ('LOGIN', '登录'),
    ('LOGOUT', '登出'),
    ('APPROVE', '审批'),
    ('REJECT', '拒绝'),
    ('EXPORT', '导出'),
)

class OperationLog(models.Model):
    """操作日志模型"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="operation_logs", db_column='user_id_id')
    user_code = models.CharField(max_length=20, null=True, blank=True, db_column='user_code')  # 保存用户ID（字符串），即使用户被删除也能查看
    user_name = models.CharField(max_length=50, null=True, blank=True)  # 保存用户名
    action_type = models.CharField(max_length=20, choices=ACTION_TYPE_CHOICES)
    module = models.CharField(max_length=50)  # 模块名称，如：员工管理、考勤管理
    resource_type = models.CharField(max_length=50, null=True, blank=True)  # 资源类型，如：EmployeeProfile、AttendanceRecord
    resource_id = models.CharField(max_length=100, null=True, blank=True)  # 资源ID
    description = models.TextField()  # 操作描述
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # IP地址
    user_agent = models.CharField(max_length=255, null=True, blank=True)  # 用户代理
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "operation_log"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user_code', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
            models.Index(fields=['module', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user_name or self.user_code} - {self.get_action_type_display()} - {self.module}"

# 招聘管理相关枚举
RECRUITMENT_STATUS_CHOICES = (
    ("DRAFT", "草稿"),
    ("PUBLISHED", "已发布"),
    ("CLOSED", "已关闭"),
    ("CANCELLED", "已取消"),
)

RESUME_STATUS_CHOICES = (
    ("NEW", "新简历"),
    ("SCREENING", "筛选中"),
    ("INTERVIEW", "面试中"),
    ("OFFER", "待录用"),
    ("HIRED", "已录用"),
    ("REJECTED", "已拒绝"),
)

INTERVIEW_STATUS_CHOICES = (
    ("SCHEDULED", "已安排"),
    ("IN_PROGRESS", "进行中"),
    ("COMPLETED", "已完成"),
    ("CANCELLED", "已取消"),
)

INTERVIEW_RESULT_CHOICES = (
    ("PENDING", "待定"),
    ("PASS", "通过"),
    ("FAIL", "未通过"),
    ("RESCHEDULE", "重新安排"),
)

OFFER_STATUS_CHOICES = (
    ("PENDING", "待发送"),
    ("SENT", "已发送"),
    ("ACCEPTED", "已接受"),
    ("REJECTED", "已拒绝"),
    ("EXPIRED", "已过期"),
)

# 招聘需求
class RecruitmentRequirement(models.Model):
    """招聘需求"""
    title = models.CharField(max_length=200, verbose_name="职位名称")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="recruitment_requirements", verbose_name="部门")
    position = models.ForeignKey(JobPosition, null=True, blank=True, on_delete=models.SET_NULL, related_name="recruitment_requirements", verbose_name="岗位")
    number = models.IntegerField(default=1, verbose_name="招聘人数")
    requirements = models.TextField(null=True, blank=True, verbose_name="任职要求")
    description = models.TextField(null=True, blank=True, verbose_name="职位描述")
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="最低薪资")
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="最高薪资")
    status = models.CharField(max_length=20, choices=RECRUITMENT_STATUS_CHOICES, default="DRAFT", verbose_name="状态")
    publisher = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="published_recruitments", verbose_name="发布人")
    publish_time = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")
    deadline = models.DateField(null=True, blank=True, verbose_name="截止日期")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recruitment_requirement"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.department.name}"

# 简历
class Resume(models.Model):
    """简历"""
    recruitment = models.ForeignKey(RecruitmentRequirement, on_delete=models.CASCADE, related_name="resumes", verbose_name="招聘需求")
    name = models.CharField(max_length=50, verbose_name="姓名")
    gender = models.CharField(max_length=10, null=True, blank=True, verbose_name="性别")
    phone = models.CharField(max_length=30, verbose_name="手机号")
    email = models.CharField(max_length=100, null=True, blank=True, verbose_name="邮箱")
    education = models.CharField(max_length=50, null=True, blank=True, verbose_name="学历")
    work_experience = models.TextField(null=True, blank=True, verbose_name="工作经历")
    skills = models.TextField(null=True, blank=True, verbose_name="技能特长")
    resume_file = models.FileField(upload_to='resumes/', null=True, blank=True, verbose_name="简历文件")
    status = models.CharField(max_length=20, choices=RESUME_STATUS_CHOICES, default="NEW", verbose_name="状态")
    source = models.CharField(max_length=50, null=True, blank=True, verbose_name="简历来源")
    note = models.TextField(null=True, blank=True, verbose_name="备注")
    recruiter = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="handled_resumes", verbose_name="处理人")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resume"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.recruitment.title}"

# 面试
class Interview(models.Model):
    """面试"""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="interviews", verbose_name="简历")
    round = models.IntegerField(default=1, verbose_name="面试轮次")
    interview_type = models.CharField(max_length=50, null=True, blank=True, verbose_name="面试类型")  # 初试、复试、终试等
    scheduled_time = models.DateTimeField(verbose_name="面试时间")
    location = models.CharField(max_length=200, null=True, blank=True, verbose_name="面试地点")
    interviewers = models.ManyToManyField(User, related_name="interviews", verbose_name="面试官")
    status = models.CharField(max_length=20, choices=INTERVIEW_STATUS_CHOICES, default="SCHEDULED", verbose_name="状态")
    result = models.CharField(max_length=20, choices=INTERVIEW_RESULT_CHOICES, null=True, blank=True, verbose_name="面试结果")
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="评分")
    comment = models.TextField(null=True, blank=True, verbose_name="面试评价")
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_interviews", verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "interview"
        ordering = ['-scheduled_time']

    def __str__(self):
        return f"{self.resume.name} - 第{self.round}轮面试 - {self.scheduled_time}"

# 录用
class Offer(models.Model):
    """录用Offer"""
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name="offer", verbose_name="简历")
    position = models.ForeignKey(JobPosition, null=True, blank=True, on_delete=models.SET_NULL, related_name="offers", verbose_name="岗位")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="offers", verbose_name="部门")
    salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="薪资")
    start_date = models.DateField(null=True, blank=True, verbose_name="入职日期")
    status = models.CharField(max_length=20, choices=OFFER_STATUS_CHOICES, default="PENDING", verbose_name="状态")
    content = models.TextField(null=True, blank=True, verbose_name="Offer内容")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="有效期至")
    sent_time = models.DateTimeField(null=True, blank=True, verbose_name="发送时间")
    accepted_time = models.DateTimeField(null=True, blank=True, verbose_name="接受时间")
    rejected_reason = models.TextField(null=True, blank=True, verbose_name="拒绝原因")
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_offers", verbose_name="创建人")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "offer"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.resume.name} - {self.department.name} - {self.status}"