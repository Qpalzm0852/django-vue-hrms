from rest_framework import serializers
from rest_framework.fields import DateTimeField
from . import models as md


# 序列化

class SuperUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = md.User
        fields = ['user_id', 'name', 'password', 'is_admin']

    def create(self, validated_data):
        instance = md.User.objects.create_superuser(**validated_data)
        return instance

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.set_password(validated_data.get('password'))
        instance.save()

        return instance


# 旧的教务系统序列化器已注释，因为模型已改为HR系统
# class CollegeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = md.CollegeTable
#         fields = ['college_id', 'college_name']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = md.User
        fields = ['user_id', 'name', 'password']


# class StudentSerializer(serializers.ModelSerializer):
#     user = UserSerializer(required=False)
#     college = serializers.CharField(
#         source="college.college_id", required=False)
#     class Meta:
#         model = md.StudentTable
#         fields = ['user', 'English_class', 'college']


# class TeacherSerializer(serializers.ModelSerializer):
#     user = UserSerializer()
#     college = serializers.CharField(source="college.college_id")
#     class Meta:
#         model = md.TeacherTable
#         fields = ['user', 'position', 'college']


# class CourseSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = md.CourseTable
#         fields = ['course_id', 'course_name', 'credit']


# class OpenSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = md.OpenTable
#         fields = ['id', 'course', 'teacher', 'semester', 'course_time']


# class OpenDetailSerializer(serializers.ModelSerializer):
#     course = CourseSerializer()
#     teacher = TeacherSerializer()
#     class Meta:
#         model = md.OpenTable
#         fields = ['id', 'course', 'teacher', 'semester', 'course_time']


# class ScoreSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = md.ScoreTable
#         fields = ['student', 'open', 'score']


# class ScoreDetailSerializer(serializers.ModelSerializer):
#     student = StudentSerializer()
#     open = OpenDetailSerializer()
#     class Meta:
#         model = md.ScoreTable
#         fields = ['student', 'open', 'score']


# class ScoreDetailSerializer_v2(serializers.ModelSerializer):
#     open = OpenDetailSerializer()
#     class Meta:
#         model = md.ScoreTable
#         fields = ['open', 'score']


# ============ 企业人力资源管理系统序列化器 ============

class PermissionControlMixin:
    """字段级权限控制混入类"""

    role_hidden_fields = {
        'ADMIN': [],
        'HR': [],
        'MANAGER': [],
        'STAFF': [],
    }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        role = (getattr(getattr(request, 'user', None), 'role', '') or '').upper()
        hidden_fields = self.role_hidden_fields.get(role, self.role_hidden_fields.get('STAFF', []))
        for field_name in hidden_fields:
            data.pop(field_name, None)
        return data


class DepartmentSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source='manager.name', read_only=True)
    
    class Meta:
        model = md.Department
        fields = '__all__'


class JobPositionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = md.JobPosition
        fields = '__all__'


class EmployeeProfileSerializer(PermissionControlMixin, serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_id = serializers.CharField(source='user.user_id', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_name = serializers.CharField(source='position.name', read_only=True)
    # 允许在创建时通过 user_id, name, password, role 创建用户
    # 注意：这里不能使用 user_id，因为上面已经定义了只读的 user_id
    # 所以我们通过重写 to_internal_value 来处理 user_id 字段
    name = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)

    role_hidden_fields = {
        'ADMIN': [],
        'HR': ['id_no'],
        'MANAGER': ['id_no', 'base_salary', 'contract_end'],
        'STAFF': ['id_no', 'base_salary'],
    }

    class Meta:
        model = md.EmployeeProfile
        fields = '__all__'
        extra_kwargs = {
            'user': {'write_only': False, 'required': False},  # 在创建时不需要直接传入user对象
        }
    
    def to_internal_value(self, data):
        """处理前端传递的 user_id 和 role 字段"""
        # 如果前端传递了 user_id，我们需要在 validated_data 中处理它
        # 由于 user_id 是只读字段，我们需要手动提取它
        user_id = data.get('user_id')
        role = data.get('role')
        validated_data = super().to_internal_value(data)
        if user_id and 'user' not in validated_data:
            # 将 user_id 存储到临时位置，以便在 create 方法中使用
            validated_data['_user_id'] = user_id
        if role:
            # 将 role 存储到 validated_data 中，以便在 create 方法中使用
            validated_data['role'] = role
        return validated_data
    
    def create(self, validated_data):
        """创建员工档案，如果用户不存在则先创建用户"""
        # 从 validated_data 中提取 user_id（如果存在）
        user_id = validated_data.pop('_user_id', None)
        name = validated_data.pop('name', None)
        password = validated_data.pop('password', None)
        role_value = validated_data.pop('role', 'STAFF')
        
        # 如果 user 字段存在，说明用户已经存在
        if 'user' in validated_data and validated_data['user']:
            user = validated_data.pop('user')
            if isinstance(user, md.User):
                # 如果传入了 name 或 password，更新用户
                if name:
                    user.name = name
                if password:
                    user.set_password(password)
                if role_value:
                    user.role = role_value
                user.save()
                validated_data['user'] = user
            elif isinstance(user, str):
                # 如果 user 是字符串（user_id），获取用户
                user_id = user
        
        if not user_id:
            raise serializers.ValidationError("user_id 是必填字段")
        
        # 获取或创建用户
        try:
            user = md.User.objects.get(user_id=user_id)
            # 如果用户已存在，更新用户信息
            if name:
                user.name = name
            if password:
                user.set_password(password)
            if role_value:
                user.role = role_value
            user.save()
        except md.User.DoesNotExist:
            # 用户不存在，创建新用户
            if not name:
                raise serializers.ValidationError("创建新用户时，name 是必填字段")
            if not password:
                raise serializers.ValidationError("创建新用户时，password 是必填字段")
            user = md.User.objects.create_user(
                user_id=user_id,
                name=name,
                password=password,
                role=role_value
            )
        
        validated_data['user'] = user
        # 创建员工档案
        return super().create(validated_data)
    



class NullableDateTimeField(DateTimeField):
    """可空的日期时间字段，允许无效值转换为 None"""
    def to_internal_value(self, value):
        if not value or value == '':
            return None
        # 如果是无效的字符串格式，返回 None
        if isinstance(value, str) and len(value.strip()) < 10:
            return None
        try:
            return super().to_internal_value(value)
        except (ValueError, TypeError):
            # 如果解析失败，返回 None
            return None


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """考勤记录序列化器"""

    employee_id = serializers.CharField(source='employee.user_id', read_only=True)
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    # 允许通过工号（user_id）来设置employee字段
    employee = serializers.CharField(write_only=True, required=True)
    # 使用自定义的可空日期时间字段
    check_in = NullableDateTimeField(required=False, allow_null=True)
    check_out = NullableDateTimeField(required=False, allow_null=True)

    class Meta:
        model = md.AttendanceRecord
        fields = '__all__'
        extra_kwargs = {
            'work_hours': {'required': False, 'allow_null': True},
            'overtime_hours': {'required': False, 'allow_null': True},
        }

    def validate_employee(self, value):
        """验证员工工号是否存在"""
        try:
            user = md.User.objects.get(user_id=value)
            return user
        except md.User.DoesNotExist:
            raise serializers.ValidationError(f"工号 {value} 不存在")

    def create(self, validated_data):
        """创建考勤记录"""
        # employee 字段已经在 validate_employee 中转换为 User 对象
        return super().create(validated_data)


# 请假申请序列化器
class LeaveRequestSerializer(serializers.ModelSerializer):
    """请假申请序列化器"""
    employee_id = serializers.CharField(source='employee.user_id', read_only=True)
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    approver_id = serializers.CharField(source='approver.user_id', read_only=True, allow_null=True)
    approver_name = serializers.CharField(source='approver.name', read_only=True, allow_null=True)
    employee = serializers.CharField(write_only=True, required=True)
    approver = serializers.CharField(write_only=True, required=False, allow_null=True)
    start_time = NullableDateTimeField(required=True)
    end_time = NullableDateTimeField(required=True)

    class Meta:
        model = md.LeaveRequest
        fields = '__all__'
        extra_kwargs = {
            'hours': {'required': False, 'allow_null': True},
            'reason': {'required': False, 'allow_null': True},
        }

    def validate_employee(self, value):
        """验证员工工号"""
        try:
            return md.User.objects.get(user_id=value)
        except md.User.DoesNotExist:
            raise serializers.ValidationError(f"工号 {value} 不存在")

    def validate_approver(self, value):
        """验证审批人工号"""
        if not value:
            return None
        try:
            return md.User.objects.get(user_id=value)
        except md.User.DoesNotExist:
            raise serializers.ValidationError(f"审批人工号 {value} 不存在")


# 薪酬序列化器
class PayrollSerializer(serializers.ModelSerializer):
    """薪酬序列化器"""
    employee_id = serializers.CharField(source='employee.user_id', read_only=True)
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    employee = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = md.Payroll
        fields = '__all__'

    def validate_employee(self, value):
        """验证员工工号"""
        try:
            return md.User.objects.get(user_id=value)
        except md.User.DoesNotExist:
            raise serializers.ValidationError(f"工号 {value} 不存在")
    



# 绩效记录序列化器
class PerformanceRecordSerializer(serializers.ModelSerializer):
    """绩效记录序列化器"""
    employee_id = serializers.CharField(source='employee.user_id', read_only=True)
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    evaluator_id = serializers.CharField(source='evaluator.user_id', read_only=True, allow_null=True)
    evaluator_name = serializers.CharField(source='evaluator.name', read_only=True, allow_null=True)
    employee = serializers.CharField(write_only=True, required=True)
    evaluator = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = md.PerformanceRecord
        fields = '__all__'
        extra_kwargs = {
            'score': {'required': False, 'allow_null': True},
            'dimension': {'required': False, 'allow_null': True},
            'comment': {'required': False, 'allow_null': True},
        }

    def validate_employee(self, value):
        """验证员工工号"""
        try:
            return md.User.objects.get(user_id=value)
        except md.User.DoesNotExist:
            raise serializers.ValidationError(f"工号 {value} 不存在")

    def validate_evaluator(self, value):
        """验证评估人工号"""
        if not value:
            return None
        try:
            return md.User.objects.get(user_id=value)
        except md.User.DoesNotExist:
            raise serializers.ValidationError(f"评估人工号 {value} 不存在")


# 培训序列化器
class TrainingSerializer(serializers.ModelSerializer):
    """培训序列化器"""
    start_time = NullableDateTimeField(required=False, allow_null=True)
    end_time = NullableDateTimeField(required=False, allow_null=True)
    
    class Meta:
        model = md.Training
        fields = '__all__'
        extra_kwargs = {
            'title': {'required': True},
            'content': {'required': False, 'allow_null': True},
            'participants_scope': {'required': False, 'allow_null': True},
        }


# 公告序列化器
class AnnouncementSerializer(serializers.ModelSerializer):
    """公告序列化器"""
    publisher_id = serializers.CharField(source='publisher.user_id', read_only=True, allow_null=True)
    publisher_name = serializers.CharField(source='publisher.name', read_only=True, allow_null=True)
    publisher = serializers.CharField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = md.Announcement
        fields = '__all__'
        extra_kwargs = {
            'title': {'required': True},
            'content': {'required': False, 'allow_null': True},
            'level': {'required': False, 'allow_null': True},
            'publish_time': {'read_only': True},
        }
    
    def validate_publisher(self, value):
        """验证发布人工号"""
        if not value:
            return None
        try:
            return md.User.objects.get(user_id=value)
        except md.User.DoesNotExist:
            raise serializers.ValidationError(f"发布人工号 {value} 不存在")


# 加班申请序列化器
class OvertimeRequestSerializer(serializers.ModelSerializer):
    """加班申请序列化器"""
    employee_id = serializers.CharField(source='employee.user_id', read_only=True)
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    approver_id = serializers.CharField(source='approver.user_id', read_only=True, allow_null=True)
    approver_name = serializers.CharField(source='approver.name', read_only=True, allow_null=True)
    employee = serializers.CharField(write_only=True, required=True)
    approver = serializers.CharField(write_only=True, required=False, allow_null=True)
    start_time = NullableDateTimeField(required=True)
    end_time = NullableDateTimeField(required=True)

    class Meta:
        model = md.OvertimeRequest
        fields = '__all__'
        extra_kwargs = {
            'hours': {'required': False, 'allow_null': True},
            'reason': {'required': False, 'allow_null': True},
        }

    def validate_employee(self, value):
        """验证员工工号"""
        try:
            return md.User.objects.get(user_id=value)
        except md.User.DoesNotExist:
            raise serializers.ValidationError(f"工号 {value} 不存在")

    def validate_approver(self, value):
        """验证审批人工号"""
        if not value:
            return None
        try:
            return md.User.objects.get(user_id=value)
        except md.User.DoesNotExist:
            raise serializers.ValidationError(f"审批人工号 {value} 不存在")


# 操作日志序列化器
class OperationLogSerializer(serializers.ModelSerializer):
    """操作日志序列化器"""
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)

    class Meta:
        model = md.OperationLog
        fields = '__all__'


# 招聘管理序列化器

class RecruitmentRequirementSerializer(serializers.ModelSerializer):
    """招聘需求序列化器"""
    department_name = serializers.SerializerMethodField()
    position_name = serializers.SerializerMethodField()
    publisher_name = serializers.SerializerMethodField()
    department = serializers.CharField(write_only=True, required=True)
    position = serializers.CharField(write_only=True, required=False, allow_null=True)
    
    def get_department_name(self, obj):
        """获取部门名称"""
        return obj.department.name if obj.department else None
    
    def get_position_name(self, obj):
        """获取岗位名称"""
        return obj.position.name if obj.position else None
    
    def get_publisher_name(self, obj):
        """获取发布人名称"""
        return obj.publisher.name if obj.publisher else None
    
    class Meta:
        model = md.RecruitmentRequirement
        fields = '__all__'
        extra_kwargs = {
            'publisher': {'write_only': False, 'required': False},
            'publish_time': {'read_only': True},
        }
    
    def validate_department(self, value):
        """验证部门名称"""
        try:
            return md.Department.objects.get(name=value)
        except md.Department.DoesNotExist:
            raise serializers.ValidationError(f"部门 '{value}' 不存在")
    
    def validate_position(self, value):
        """验证岗位名称"""
        if not value:
            return None
        try:
            department = self.initial_data.get('department')
            if department:
                dept = md.Department.objects.get(name=department)
                position = md.JobPosition.objects.filter(name=value, department=dept).first()
                if position:
                    return position
            raise serializers.ValidationError(f"岗位 '{value}' 不存在")
        except md.Department.DoesNotExist:
            raise serializers.ValidationError(f"部门不存在")


class ResumeSerializer(serializers.ModelSerializer):
    """简历序列化器"""
    recruitment_title = serializers.CharField(source='recruitment.title', read_only=True)
    recruitment_id = serializers.IntegerField(source='recruitment.id', read_only=True)
    recruiter_name = serializers.CharField(source='recruiter.name', read_only=True, allow_null=True)
    recruitment = serializers.IntegerField(write_only=True, required=True)
    recruiter = serializers.CharField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = md.Resume
        fields = '__all__'
        extra_kwargs = {
            'resume_file': {'required': False, 'allow_null': True},
        }
    
    def validate_recruitment(self, value):
        """验证招聘需求ID"""
        try:
            return md.RecruitmentRequirement.objects.get(id=value)
        except md.RecruitmentRequirement.DoesNotExist:
            raise serializers.ValidationError(f"招聘需求 ID {value} 不存在")
    
    def validate_recruiter(self, value):
        """验证处理人工号"""
        if not value:
            return None
        try:
            return md.User.objects.get(user_id=value)
        except md.User.DoesNotExist:
            raise serializers.ValidationError(f"处理人工号 {value} 不存在")


class InterviewSerializer(serializers.ModelSerializer):
    """面试序列化器"""
    resume_name = serializers.CharField(source='resume.name', read_only=True)
    resume_id = serializers.IntegerField(source='resume.id', read_only=True)
    resume_phone = serializers.CharField(source='resume.phone', read_only=True)
    interviewers_info = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.name', read_only=True, allow_null=True)
    resume = serializers.IntegerField(write_only=True, required=True)
    created_by = serializers.CharField(write_only=True, required=False, allow_null=True)
    interviewer_ids = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        allow_null=True
    )
    scheduled_time = NullableDateTimeField(required=True)
    
    class Meta:
        model = md.Interview
        fields = '__all__'
        extra_kwargs = {
            'interviewers': {'read_only': True},
        }
    
    def get_interviewers_info(self, obj):
        """获取面试官信息"""
        if obj.interviewers.exists():
            return [
                {'user_id': interviewer.user_id, 'name': interviewer.name}
                for interviewer in obj.interviewers.all()
            ]
        return []
    
    def validate_resume(self, value):
        """验证简历ID"""
        try:
            return md.Resume.objects.get(id=value)
        except md.Resume.DoesNotExist:
            raise serializers.ValidationError(f"简历 ID {value} 不存在")
    
    def validate_created_by(self, value):
        """验证创建人工号"""
        if not value:
            return None
        try:
            return md.User.objects.get(user_id=value)
        except md.User.DoesNotExist:
            raise serializers.ValidationError(f"创建人工号 {value} 不存在")
    
    def create(self, validated_data):
        """创建面试记录"""
        interviewer_ids = validated_data.pop('interviewer_ids', [])
        interview = super().create(validated_data)
        if interviewer_ids:
            interviewers = md.User.objects.filter(user_id__in=interviewer_ids)
            interview.interviewers.set(interviewers)
        return interview
    
    def update(self, instance, validated_data):
        """更新面试记录"""
        interviewer_ids = validated_data.pop('interviewer_ids', None)
        interview = super().update(instance, validated_data)
        if interviewer_ids is not None:
            interviewers = md.User.objects.filter(user_id__in=interviewer_ids)
            interview.interviewers.set(interviewers)
        return interview


class OfferSerializer(serializers.ModelSerializer):
    """录用Offer序列化器"""
    resume_name = serializers.CharField(source='resume.name', read_only=True)
    resume_id = serializers.IntegerField(source='resume.id', read_only=True)
    resume_phone = serializers.CharField(source='resume.phone', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    position_name = serializers.CharField(source='position.name', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True, allow_null=True)
    department = serializers.CharField(write_only=True, required=True)
    position = serializers.CharField(write_only=True, required=False, allow_null=True)
    resume = serializers.IntegerField(write_only=True, required=True)
    created_by = serializers.CharField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = md.Offer
        fields = '__all__'
        extra_kwargs = {
            'sent_time': {'read_only': True},
            'accepted_time': {'read_only': True},
        }
    
    def validate_department(self, value):
        """验证部门名称"""
        try:
            return md.Department.objects.get(name=value)
        except md.Department.DoesNotExist:
            raise serializers.ValidationError(f"部门 '{value}' 不存在")
    
    def validate_position(self, value):
        """验证岗位名称"""
        if not value:
            return None
        try:
            department = self.initial_data.get('department')
            if department:
                dept = md.Department.objects.get(name=department)
                position = md.JobPosition.objects.filter(name=value, department=dept).first()
                if position:
                    return position
            raise serializers.ValidationError(f"岗位 '{value}' 不存在")
        except md.Department.DoesNotExist:
            raise serializers.ValidationError(f"部门不存在")
    
    def validate_resume(self, value):
        """验证简历ID"""
        try:
            resume = md.Resume.objects.get(id=value)
            # 检查是否已有offer
            if hasattr(resume, 'offer'):
                raise serializers.ValidationError(f"该简历已存在录用记录")
            return resume
        except md.Resume.DoesNotExist:
            raise serializers.ValidationError(f"简历 ID {value} 不存在")
    
    def validate_created_by(self, value):
        """验证创建人工号"""
        if not value:
            return None
        try:
            return md.User.objects.get(user_id=value)
        except md.User.DoesNotExist:
            raise serializers.ValidationError(f"创建人工号 {value} 不存在")

