<template>
  <div class="biz-page">
    <section class="biz-page__hero">
      <div class="biz-page__hero-copy">
        <p class="biz-page__eyebrow">Employee Directory</p>
        <h1 class="biz-page__title">员工档案</h1>
        <p class="biz-page__description">
          管理员工基础档案、岗位与状态信息，支持按字段检索、Excel 导入导出，以及新增和编辑员工资料。
        </p>
        <div class="biz-page__meta">
          <span class="biz-page__badge">员工总数 {{ total }} 人</span>
          <span class="biz-page__badge">当前页 {{ studentListShow.length }} 人</span>
        </div>
      </div>
      <div class="biz-page__hero-side">
        <div class="biz-page__stat">
          <p class="biz-page__stat-label">在职员工</p>
          <p class="biz-page__stat-value">{{ onboardCount }}</p>
        </div>
      </div>
    </section>

    <el-card class="biz-page__panel">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-main">
          <h2 class="biz-page__toolbar-title">员工档案列表</h2>
          <p class="biz-page__toolbar-desc">通过字段筛选快速定位员工，并在右侧执行导入、导出和新增操作。</p>
        </div>
        <div class="biz-page__toolbar-actions">
          <el-button type="info" icon="el-icon-upload2" @click="importDialogVisible = true">导入Excel</el-button>
          <el-button type="success" icon="el-icon-download" :loading="exporting" :disabled="exporting" @click="exportToExcel">导出Excel</el-button>
          <el-button type="primary" @click="addDialogVisible = true">添加员工</el-button>
        </div>
      </div>

      <div v-if="operationFeedback" class="operation-feedback" :class="{ 'is-error': operationFeedback.status === 'error' }">
        <div class="operation-feedback__header">
          <span class="operation-feedback__title">操作结果反馈</span>
          <el-tag :type="operationFeedback.status === 'success' ? 'success' : 'danger'" size="small">{{ operationFeedback.result }}</el-tag>
        </div>
        <div class="operation-feedback__grid">
          <div class="operation-feedback__item">
            <span>功能模块</span>
            <strong>{{ operationFeedback.module }}</strong>
          </div>
          <div class="operation-feedback__item">
            <span>操作类型</span>
            <strong>{{ operationFeedback.action }}</strong>
          </div>
          <div class="operation-feedback__item">
            <span>操作时间</span>
            <strong>{{ operationFeedback.time }}</strong>
          </div>
          <div v-if="operationFeedback.count !== undefined && operationFeedback.count !== null" class="operation-feedback__item">
            <span>记录数量</span>
            <strong>{{ operationFeedback.countText || ('共 ' + operationFeedback.count + ' 条记录') }}</strong>
          </div>
          <div v-if="operationFeedback.filename" class="operation-feedback__item">
            <span>文件名称</span>
            <strong>{{ operationFeedback.filename }}</strong>
          </div>
          <div v-if="operationFeedback.reason" class="operation-feedback__item operation-feedback__item--wide">
            <span>失败原因</span>
            <strong>{{ operationFeedback.reason }}</strong>
          </div>
          <div class="operation-feedback__item operation-feedback__item--wide">
            <span>验证说明</span>
            <strong>{{ operationFeedback.description }}</strong>
          </div>
        </div>
      </div>

      <el-form :inline="true" class="biz-page__filters">
        <el-form-item label="筛选字段">
          <el-select v-model="selected" style="width: 140px" placeholder="筛选字段">
            <el-option
              v-for="item in options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="searchFieldLabel">
          <el-input v-model="input" :placeholder="'请输入' + searchFieldLabel" clearable style="width: 260px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getStudentList(true)" />
          <el-button type="default" icon="el-icon-refresh-right" @click="getStudentList(false)" />
        </el-form-item>
      </el-form>

      <div
        v-loading="loading"
        element-loading-text="加载中..."
        element-loading-spinner="el-icon-loading"
      >
        <el-table :data="studentListShow" border stripe>
          <el-table-column type="index" label="#" width="58" />
          <el-table-column prop="user_id" label="工号" min-width="110" />
          <el-table-column prop="user_name" label="姓名" min-width="110" />
          <el-table-column prop="role" label="角色" min-width="110">
            <template slot-scope="scope">
              <el-tag size="mini" effect="plain" :type="getRoleTagType(scope.row.role)">
                {{ getRoleLabel(scope.row.role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="department_name" label="部门" min-width="120" />
          <el-table-column prop="position_name" label="岗位" min-width="120" />
          <el-table-column prop="status" label="状态" min-width="110">
            <template slot-scope="scope">
              <el-tag size="mini" effect="dark" :type="getStatusTagType(scope.row.status)">
                {{ getStatusLabel(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="电话" min-width="130" />
          <el-table-column label="操作" width="124" align="center" fixed="right">
            <template slot-scope="scope">
              <el-button
                class="row-action-btn"
                type="primary"
                icon="el-icon-edit"
                size="mini"
                @click="showEditDialog(scope.row.user_id)"
              />
              <el-button
                class="row-action-btn"
                type="danger"
                icon="el-icon-delete"
                size="mini"
                @click="deleteStudent(scope.row.user_id)"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-if="!loading && !studentListShow.length" class="biz-page__table-empty">
        <p class="biz-page__table-empty-title">当前没有员工记录</p>
        <p class="biz-page__table-empty-desc">可以调整筛选条件，或使用右上角操作导入和新增员工。</p>
      </div>

      <el-pagination
        class="biz-page__pagination"
        :current-page="currentPage"
        :page-sizes="[10, 15, 20, 30]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>

    <el-dialog title="添加员工" :visible.sync="addDialogVisible" width="60%" @close="addDialogClosed">
      <el-form ref="addFormRef" label-position="left" :model="addForm" :rules="addFormRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工号" prop="user_id">
              <el-input v-model="addForm.user_id" placeholder="请输入工号" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="addForm.name" placeholder="请输入姓名" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="密码" prop="password">
              <el-input v-model="addForm.password" placeholder="请输入密码" show-password clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="角色" prop="role">
              <el-select v-model="addForm.role" placeholder="请选择角色" style="width: 100%">
                <el-option label="管理员" value="ADMIN" />
                <el-option label="HR" value="HR" />
                <el-option label="经理" value="MANAGER" />
                <el-option label="员工" value="STAFF" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="部门" prop="department">
              <el-select v-model="addForm.department" placeholder="请选择部门" style="width: 100%">
                <el-option
                  v-for="item in departmentList"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="岗位" prop="position">
              <el-select v-model="addForm.position" placeholder="请选择岗位" style="width: 100%" clearable>
                <el-option
                  v-for="item in positionList"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="电话" prop="phone">
              <el-input v-model="addForm.phone" placeholder="请输入电话" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="addForm.email" placeholder="请输入邮箱" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="入职日期" prop="hire_date">
              <el-date-picker
                v-model="addForm.hire_date"
                type="date"
                placeholder="选择入职日期"
                style="width: 100%"
                value-format="yyyy-MM-dd"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="addForm.status" placeholder="请选择状态" style="width: 100%">
                <el-option label="在职" value="ONBOARD" />
                <el-option label="试用" value="PROBATION" />
                <el-option label="离职" value="LEAVE" />
                <el-option label="停薪留职" value="SUSPEND" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <span slot="footer" class="dialog-footer">
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="submitting" @click="addStudent">确定</el-button>
      </span>
    </el-dialog>

    <el-dialog title="修改员工信息" :visible.sync="editDialogVisible" width="60%" @close="editDialogClosed">
      <el-form ref="editFormRef" label-position="left" :model="editForm" :rules="editFormRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工号" prop="user_id">
              <el-input v-model="editForm.user_id" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" prop="user_name">
              <el-input v-model="editForm.user_name" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="部门" prop="department">
              <el-select v-model="editForm.department" placeholder="请选择部门" style="width: 100%">
                <el-option
                  v-for="item in departmentList"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="岗位" prop="position">
              <el-select v-model="editForm.position" placeholder="请选择岗位" style="width: 100%" clearable>
                <el-option
                  v-for="item in positionList"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="电话" prop="phone">
              <el-input v-model="editForm.phone" placeholder="请输入电话" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="editForm.email" placeholder="请输入邮箱" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="入职日期" prop="hire_date">
              <el-date-picker
                v-model="editForm.hire_date"
                type="date"
                placeholder="选择入职日期"
                style="width: 100%"
                value-format="yyyy-MM-dd"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="editForm.status" placeholder="请选择状态" style="width: 100%">
                <el-option label="在职" value="ONBOARD" />
                <el-option label="试用" value="PROBATION" />
                <el-option label="离职" value="LEAVE" />
                <el-option label="停薪留职" value="SUSPEND" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <span slot="footer" class="dialog-footer">
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="submitting" @click="editStudent">确定</el-button>
      </span>
    </el-dialog>

    <el-dialog title="导入员工信息" :visible.sync="importDialogVisible" width="50%" @close="importDialogClosed">
      <div style="margin-bottom: 20px">
        <el-alert title="导入说明" type="info" :closable="false" show-icon>
          <div slot="description">
            <p>1. 请使用系统模板并按列填写数据。</p>
            <p>2. 必填列：工号、姓名、部门、密码。</p>
            <p>3. 部门名称必须与系统中已存在的部门完全一致。</p>
            <p>4. 如果员工已存在，系统会更新其信息。</p>
          </div>
        </el-alert>
      </div>

      <el-upload
        ref="upload"
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="importFileList"
        :limit="1"
        accept=".xlsx,.xls"
        drag
      >
        <i class="el-icon-upload" />
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <div slot="tip" class="el-upload__tip">只能上传 xlsx/xls 文件，且不超过 10MB</div>
      </el-upload>

      <div v-if="importResult" style="margin-top: 20px">
        <el-alert
          :title="importResult.message"
          :type="importResult.fail_count > 0 ? 'warning' : 'success'"
          :closable="false"
          show-icon
        >
          <div slot="description">
            <p>成功: {{ importResult.success_count }} 条</p>
            <p>失败: {{ importResult.fail_count }} 条</p>
            <p>总计: {{ importResult.total }} 条</p>
            <div v-if="importResult.errors && importResult.errors.length > 0" style="margin-top: 10px">
              <p style="font-weight: bold">错误详情：</p>
              <ul style="margin: 5px 0; padding-left: 20px">
                <li v-for="(error, index) in importResult.errors" :key="index">
                  第 {{ error.row }} 行: {{ error.error }}
                </li>
              </ul>
            </div>
          </div>
        </el-alert>
      </div>

      <span slot="footer" class="dialog-footer">
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="handleImport">开始导入</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { exportToExcel } from '@/utils/excelExport'
import { getErrorMessage } from '@/utils/errorHandler'

export default {
  data() {
    return {
      options: [
        { value: 'user_id', label: '工号' },
        { value: 'user_name', label: '姓名' },
        { value: 'department_name', label: '部门' },
      ],
      selected: 'user_id',
      input: '',
      loading: false,
      exporting: false,
      submitting: false,
      studentList: [],
      studentListShow: [],
      departmentList: [],
      positionList: [],
      total: 0,
      currentPage: 1,
      pageSize: 10,
      addDialogVisible: false,
      editDialogVisible: false,
      importDialogVisible: false,
      importFileList: [],
      importFile: null,
      importing: false,
      importResult: null,
      operationFeedback: null,
      addForm: {
        user_id: '',
        name: '',
        password: '',
        role: 'STAFF',
        department: '',
        position: '',
        phone: '',
        email: '',
        hire_date: '',
        status: 'ONBOARD',
      },
      addFormRules: {
        user_id: [
          { required: true, message: '请输入工号', trigger: 'blur' },
          { min: 3, max: 20, message: '工号长度应为 3-20 个字符', trigger: 'blur' },
        ],
        name: [
          { required: true, message: '请输入姓名', trigger: 'blur' },
          { min: 2, max: 50, message: '姓名长度应为 2-50 个字符', trigger: 'blur' },
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, max: 128, message: '密码长度应为 6-128 个字符', trigger: 'blur' },
        ],
        role: [{ required: true, message: '请选择角色', trigger: 'change' }],
        department: [{ required: true, message: '请选择部门', trigger: 'change' }],
        status: [{ required: true, message: '请选择状态', trigger: 'change' }],
      },
      editForm: {
        user_id: '',
        user_name: '',
        department: '',
        position: '',
        phone: '',
        email: '',
        hire_date: '',
        status: 'ONBOARD',
      },
      editFormRules: {
        department: [{ required: true, message: '请选择部门', trigger: 'change' }],
        status: [{ required: true, message: '请选择状态', trigger: 'change' }],
      },
    }
  },
  computed: {
    onboardCount() {
      return this.studentList.filter((item) => item && item.status === 'ONBOARD').length
    },
    searchFieldLabel() {
      const item = this.options.find((opt) => opt.value === this.selected)
      return item ? item.label : ''
    },
  },
  created() {
    this.getDepartmentList()
    this.getPositionList()
    this.getStudentList()
  },
  methods: {
    formatOperationTime() {
      const date = new Date()
      const pad = (value) => String(value).padStart(2, '0')
      return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
    },
    setOperationFeedback(feedback) {
      this.operationFeedback = {
        time: this.formatOperationTime(),
        ...feedback,
      }
    },
    getRoleLabel(role) {
      const map = {
        ADMIN: '管理员',
        HR: 'HR',
        MANAGER: '经理',
        STAFF: '员工',
      }
      return map[role] || role || '-'
    },
    getRoleTagType(role) {
      const map = {
        ADMIN: 'danger',
        HR: 'warning',
        MANAGER: 'success',
        STAFF: 'info',
      }
      return map[role] || 'info'
    },
    getStatusLabel(status) {
      const map = {
        ONBOARD: '在职',
        PROBATION: '试用',
        LEAVE: '离职',
        SUSPEND: '停薪留职',
      }
      return map[status] || status || '-'
    },
    getStatusTagType(status) {
      const map = {
        ONBOARD: 'success',
        PROBATION: 'warning',
        LEAVE: 'info',
        SUSPEND: 'danger',
      }
      return map[status] || 'info'
    },
    refreshPageData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.studentListShow = this.studentList.slice(start, end)
    },
    async getDepartmentList() {
      try {
        const { data: res } = await this.$http.get('api/departments/')
        if (Array.isArray(res)) {
          this.departmentList = res
        }
      } catch (error) {
        console.error('获取部门列表失败:', error)
      }
    },
    async getPositionList() {
      try {
        const { data: res } = await this.$http.get('api/positions/')
        if (Array.isArray(res)) {
          this.positionList = res
        }
      } catch (error) {
        console.error('获取岗位列表失败:', error)
      }
    },
    async getStudentList(search = false) {
      this.loading = true
      try {
        const { data: res } = await this.$http.get('api/employees/')
        if (!Array.isArray(res)) {
          this.$message.error('获取员工列表失败')
          return
        }

        let list = res
        if (search && this.input) {
          const keyword = String(this.input).trim()
          if (keyword) {
            list = res.filter((item) => {
              const value = item[this.selected]
              return value !== null && value !== undefined && String(value).includes(keyword)
            })
          }
        }

        this.studentList = list
        this.total = list.length
        this.currentPage = 1
        this.refreshPageData()
      } catch (error) {
        console.error('获取员工列表失败:', error)
        this.$message.error(getErrorMessage(error, '获取员工列表失败'))
      } finally {
        this.loading = false
      }
    },
    addDialogClosed() {
      if (this.$refs.addFormRef) {
        this.$refs.addFormRef.resetFields()
      }
    },
    addStudent() {
      if (this.submitting) {
        return
      }
      this.$refs.addFormRef.validate(async (valid) => {
        if (!valid) {
          return
        }
        this.submitting = true
        try {
          await this.$http.post('api/employees/', {
            user_id: this.addForm.user_id,
            name: this.addForm.name,
            password: this.addForm.password,
            role: this.addForm.role,
            department: this.addForm.department,
            position: this.addForm.position || null,
            phone: this.addForm.phone || '',
            email: this.addForm.email || '',
            hire_date: this.addForm.hire_date || null,
            status: this.addForm.status,
          })
          this.$message.success('员工档案保存成功')
          this.addDialogVisible = false
          this.getStudentList(false)
        } catch (error) {
          console.error('添加员工失败:', error)
          this.$message.error(getErrorMessage(error, '添加员工失败'))
        } finally {
          this.submitting = false
        }
      })
    },
    async showEditDialog(id) {
      this.editDialogVisible = true
      try {
        const { data: res } = await this.$http.get(`api/employees/${id}/`)
        this.editForm.user_id = res.user_id
        this.editForm.user_name = res.user_name
        this.editForm.department = res.department
        this.editForm.position = res.position || ''
        this.editForm.phone = res.phone || ''
        this.editForm.email = res.email || ''
        this.editForm.hire_date = res.hire_date || ''
        this.editForm.status = res.status || 'ONBOARD'
      } catch (error) {
        console.error('获取员工信息失败:', error)
        this.$message.error(getErrorMessage(error, '获取员工信息失败'))
        this.editDialogVisible = false
      }
    },
    editDialogClosed() {
      if (this.$refs.editFormRef) {
        this.$refs.editFormRef.resetFields()
      }
    },
    editStudent() {
      if (this.submitting) {
        return
      }
      this.$refs.editFormRef.validate(async (valid) => {
        if (!valid) {
          return
        }
        this.submitting = true
        try {
          await this.$http.patch(`api/employees/${this.editForm.user_id}/`, {
            department: this.editForm.department,
            position: this.editForm.position || null,
            phone: this.editForm.phone || '',
            email: this.editForm.email || '',
            hire_date: this.editForm.hire_date || null,
            status: this.editForm.status,
          })
          this.$message.success('员工档案保存成功')
          this.editDialogVisible = false
          this.getStudentList(false)
        } catch (error) {
          console.error('更新员工信息失败:', error)
          this.$message.error(getErrorMessage(error, '更新员工信息失败'))
        } finally {
          this.submitting = false
        }
      })
    },
    deleteStudent(id) {
      this.$confirm('此操作将永久删除该员工，是否继续？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(async () => {
          try {
            await this.$http.delete(`api/employees/${id}/`)
            this.$message.success('删除员工成功')
            this.getStudentList(false)
          } catch (error) {
            console.error('删除员工失败:', error)
            this.$message.error(getErrorMessage(error, '删除员工失败'))
          }
        })
        .catch(() => {
          this.$message({
            type: 'info',
            message: '已取消删除',
          })
        })
    },
    handleSizeChange(pageSize) {
      this.pageSize = pageSize
      this.currentPage = 1
      this.refreshPageData()
    },
    handleCurrentChange(currentPage) {
      this.currentPage = currentPage
      this.refreshPageData()
    },
    async exportToExcel() {
      if (!this.studentList || this.studentList.length === 0) {
        this.$message.warning('没有数据可导出')
        return
      }

      const columns = [
        { key: 'user_id', label: '工号' },
        { key: 'user_name', label: '姓名' },
        { key: 'role', label: '角色' },
        { key: 'department_name', label: '部门' },
        { key: 'position_name', label: '岗位' },
        { key: 'status', label: '状态' },
        { key: 'phone', label: '电话' },
        { key: 'email', label: '邮箱' },
        { key: 'hire_date', label: '入职日期' },
      ]

      this.exporting = true
      this.$message.info('正在生成员工档案导出文件，请稍候...')
      try {
        const result = await exportToExcel(this.studentList, columns, '员工档案')
        if (typeof result.count === 'number') {
          this.$message.success(`员工档案导出成功，共导出 ${result.count} 条记录`)
        } else {
          this.$message.success('员工档案导出成功，文件已生成')
        }
        this.setOperationFeedback({
          module: '员工档案管理',
          action: 'Excel 导出',
          status: 'success',
          result: '导出成功',
          count: typeof result.count === 'number' ? result.count : null,
          filename: result.filename,
          description: '导出请求已完成，浏览器已生成下载文件',
        })
      } catch (error) {
        const reason = error.message || '员工档案导出失败'
        this.$message.error(reason)
        this.setOperationFeedback({
          module: '员工档案管理',
          action: 'Excel 导出',
          status: 'error',
          result: '导出失败',
          reason,
          description: '本次操作未完成，请根据错误提示检查数据或网络状态',
        })
      } finally {
        this.exporting = false
      }
    },
    handleFileChange(file, fileList) {
      this.importFile = file.raw
      this.importFileList = fileList
      this.importResult = null
    },
    async handleImport() {
      if (!this.importFile) {
        this.$message.warning('请先选择文件')
        return
      }

      const formData = new FormData()
      formData.append('file', this.importFile)

      this.importing = true
      this.$message.info('正在解析员工档案 Excel 文件，请稍候...')
      try {
        const { data: res } = await this.$http.post('/api/import/employees/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })

        if (res.success) {
          this.importResult = res
          const successCount = Number(res.success_count)
          const failCount = Number(res.fail_count)
          if (Number.isFinite(successCount) && Number.isFinite(failCount)) {
            this.$message.success(`员工档案导入完成：成功 ${successCount} 条，失败 ${failCount} 条`)
            this.setOperationFeedback({
              module: '员工档案管理',
              action: 'Excel 导入',
              status: 'success',
              result: '导入完成',
              count: successCount,
              countText: `成功 ${successCount} 条，失败 ${failCount} 条`,
              description: '员工档案导入请求已完成，页面数据已刷新',
            })
          } else {
            this.$message.success(res.message || '员工档案导入完成')
            this.setOperationFeedback({
              module: '员工档案管理',
              action: 'Excel 导入',
              status: 'success',
              result: '导入完成',
              description: '员工档案导入请求已完成，页面数据已刷新',
            })
          }
          this.getStudentList(false)
        } else {
          const reason = res.error || res.message || '员工档案导入失败'
          this.$message.error(reason)
          this.setOperationFeedback({
            module: '员工档案管理',
            action: 'Excel 导入',
            status: 'error',
            result: '导入失败',
            reason,
            description: '本次操作未完成，请根据错误提示检查数据或网络状态',
          })
        }
      } catch (error) {
        console.error('导入失败:', error)
        const reason = getErrorMessage(error, '导入员工数据失败')
        this.$message.error(reason)
        this.setOperationFeedback({
          module: '员工档案管理',
          action: 'Excel 导入',
          status: 'error',
          result: '导入失败',
          reason,
          description: '本次操作未完成，请根据错误提示检查数据或网络状态',
        })
      } finally {
        this.importing = false
      }
    },
    importDialogClosed() {
      this.importFile = null
      this.importFileList = []
      this.importResult = null
      if (this.$refs.upload) {
        this.$refs.upload.clearFiles()
      }
    },
  },
}
</script>

<style lang="less" scoped>
.operation-feedback {
  margin: 0 0 18px;
  padding: 16px 18px;
  border: 1px solid #dcdfe6;
  border-left: 4px solid #67c23a;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 6px 18px rgba(31, 45, 61, 0.06);
}

.operation-feedback.is-error {
  border-left-color: #f56c6c;
}

.operation-feedback__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.operation-feedback__title {
  font-size: 15px;
  font-weight: 700;
  color: #303133;
}

.operation-feedback__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px 18px;
}

.operation-feedback__item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.operation-feedback__item span {
  font-size: 12px;
  color: #909399;
}

.operation-feedback__item strong {
  font-size: 14px;
  color: #303133;
  font-weight: 600;
  line-height: 1.45;
  word-break: break-all;
}

.operation-feedback__item--wide {
  grid-column: 1 / -1;
}
</style>

