<template>
  <div class="biz-page">
    <section class="biz-page__hero">
      <div class="biz-page__hero-copy">
        <p class="biz-page__eyebrow">Attendance Operations</p>
        <h1 class="biz-page__title">考勤记录</h1>
        <p class="biz-page__description">
          统一管理员工打卡、工时和异常说明，支持按工号与日期筛选，并直接进行新增、统计、导入和导出操作。
        </p>
        <div class="biz-page__meta">
          <span class="biz-page__badge">考勤记录 {{ total }} 条</span>
          <span class="biz-page__badge">异常记录 {{ abnormalCount }} 条</span>
        </div>
      </div>
      <div class="biz-page__hero-side">
        <div class="biz-page__stat">
          <p class="biz-page__stat-label">当前页工时</p>
          <p class="biz-page__stat-value">{{ currentPageHours }}</p>
        </div>
      </div>
    </section>

    <el-card class="biz-page__panel">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-main">
          <h2 class="biz-page__toolbar-title">考勤列表</h2>
          <p class="biz-page__toolbar-desc">支持统计分析、Excel 导入导出和手动维护考勤记录。</p>
        </div>
        <div class="biz-page__toolbar-actions">
          <el-button type="warning" icon="el-icon-data-analysis" @click="statisticsDialogVisible = true">考勤统计</el-button>
          <el-button type="info" icon="el-icon-upload2" @click="importDialogVisible = true">导入Excel</el-button>
          <el-button type="success" icon="el-icon-download" :loading="exporting" :disabled="exporting" @click="exportToExcel">导出Excel</el-button>
          <el-button type="primary" icon="el-icon-plus" @click="addDialogVisible = true">新增考勤</el-button>
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
        <el-form-item label="工号">
          <el-input v-model="searchQuery.employee_id" placeholder="请输入工号" clearable style="width: 200px" />
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="searchQuery.work_date"
            type="date"
            placeholder="请选择日期"
            style="width: 200px"
            value-format="yyyy-MM-dd"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getAttendanceList(true)">查询</el-button>
          <el-button type="default" icon="el-icon-refresh" @click="getAttendanceList(false)">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="attendanceListShow" border stripe style="width: 100%">
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="employee_id" label="工号" min-width="110" />
        <el-table-column prop="employee_name" label="姓名" min-width="110" />
        <el-table-column prop="work_date" label="日期" min-width="120" />
        <el-table-column prop="check_in" label="上班打卡时间" min-width="160" />
        <el-table-column prop="check_out" label="下班打卡时间" min-width="160" />
        <el-table-column prop="work_hours" label="工时" min-width="90" />
        <el-table-column prop="overtime_hours" label="加班时长" min-width="90" />
        <el-table-column prop="abnormal" label="异常说明" min-width="140" />
        <el-table-column label="操作" width="110" fixed="right" align="center">
          <template slot-scope="scope">
            <div class="action-buttons">
              <el-tooltip content="编辑" placement="top">
                <el-button type="primary" icon="el-icon-edit" size="mini" circle @click="showEditDialog(scope.row)" />
              </el-tooltip>
              <el-tooltip content="删除" placement="top">
                <el-button type="danger" icon="el-icon-delete" size="mini" circle @click="deleteAttendance(scope.row)" />
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !attendanceListShow.length" class="biz-page__table-empty">
        <p class="biz-page__table-empty-title">当前没有考勤记录</p>
        <p class="biz-page__table-empty-desc">可以调整筛选条件，或通过右上角操作导入和新增考勤。</p>
      </div>

      <el-pagination
        class="biz-page__pagination"
        :current-page="currentPage"
        :page-sizes="[5, 10, 15, 20]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>

    <el-dialog title="新增考勤记录" :visible.sync="addDialogVisible" width="60%" @close="addDialogClosed">
      <el-form ref="addFormRef" :model="addForm" :rules="addFormRules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工号" prop="employee">
              <el-input v-model="addForm.employee" placeholder="请输入工号" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="日期" prop="work_date">
              <el-date-picker v-model="addForm.work_date" type="date" placeholder="选择日期" style="width: 100%" value-format="yyyy-MM-dd" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="上班打卡时间" prop="check_in">
              <el-date-picker v-model="addForm.check_in" type="datetime" placeholder="选择上班打卡时间" style="width: 100%" value-format="yyyy-MM-dd HH:mm:ss" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="下班打卡时间" prop="check_out">
              <el-date-picker v-model="addForm.check_out" type="datetime" placeholder="选择下班打卡时间" style="width: 100%" value-format="yyyy-MM-dd HH:mm:ss" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工时(小时)" prop="work_hours">
              <el-input-number v-model="addForm.work_hours" :precision="2" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="加班时长(小时)" prop="overtime_hours">
              <el-input-number v-model="addForm.overtime_hours" :precision="2" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="异常说明" prop="abnormal">
          <el-input v-model="addForm.abnormal" type="textarea" :rows="3" placeholder="请输入异常说明（可选）" />
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="submitting" @click="addAttendance">确定</el-button>
      </span>
    </el-dialog>

    <el-dialog title="修改考勤记录" :visible.sync="editDialogVisible" width="60%" @close="editDialogClosed">
      <el-form ref="editFormRef" :model="editForm" :rules="editFormRules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工号">
              <el-input v-model="editForm.employee_id" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名">
              <el-input v-model="editForm.employee_name" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="日期" prop="work_date">
              <el-date-picker v-model="editForm.work_date" type="date" placeholder="选择日期" style="width: 100%" value-format="yyyy-MM-dd" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="上班打卡时间" prop="check_in">
              <el-date-picker v-model="editForm.check_in" type="datetime" placeholder="选择上班打卡时间" style="width: 100%" value-format="yyyy-MM-dd HH:mm:ss" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="下班打卡时间" prop="check_out">
              <el-date-picker v-model="editForm.check_out" type="datetime" placeholder="选择下班打卡时间" style="width: 100%" value-format="yyyy-MM-dd HH:mm:ss" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工时(小时)" prop="work_hours">
              <el-input-number v-model="editForm.work_hours" :precision="2" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="加班时长(小时)" prop="overtime_hours">
              <el-input-number v-model="editForm.overtime_hours" :precision="2" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="异常说明" prop="abnormal">
              <el-input v-model="editForm.abnormal" type="textarea" :rows="3" placeholder="请输入异常说明（可选）" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="submitting" @click="editAttendance">确定</el-button>
      </span>
    </el-dialog>

    <el-dialog title="考勤统计" :visible.sync="statisticsDialogVisible" width="80%" @close="statisticsDialogClosed">
      <el-form :inline="true" style="margin-bottom: 20px">
        <el-form-item label="员工工号">
          <el-input v-model="statisticsForm.employee_id" placeholder="请输入员工工号" style="width: 200px" clearable />
        </el-form-item>
        <el-form-item label="统计月份">
          <el-date-picker v-model="statisticsForm.period" type="month" placeholder="选择月份" value-format="yyyy-MM" style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getStatistics" :loading="statisticsLoading">查询统计</el-button>
          <el-button type="warning" icon="el-icon-refresh-left" @click="autoDetectAbnormal" :loading="detectingAbnormal">自动识别异常</el-button>
        </el-form-item>
      </el-form>

      <div v-if="statisticsData" style="margin-top: 20px">
        <el-card shadow="hover">
          <div slot="header">
            <span style="font-weight: bold; font-size: 16px">统计概览</span>
            <span style="float: right; color: #909399">{{ statisticsData.period }} - {{ statisticsData.employee_name }}({{ statisticsData.employee_id }})</span>
          </div>
          <el-row :gutter="20">
            <el-col :span="6"><div class="stat-item"><div class="stat-label">应出勤天数</div><div class="stat-value">{{ statisticsData.work_days }}</div></div></el-col>
            <el-col :span="6"><div class="stat-item"><div class="stat-label">实际出勤天数</div><div class="stat-value">{{ statisticsData.actual_work_days }}</div></div></el-col>
            <el-col :span="6"><div class="stat-item"><div class="stat-label">缺勤天数</div><div class="stat-value" style="color: #f56c6c">{{ statisticsData.absent_days }}</div></div></el-col>
            <el-col :span="6"><div class="stat-item"><div class="stat-label">出勤率</div><div class="stat-value">{{ statisticsData.attendance_rate }}%</div></div></el-col>
          </el-row>
          <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="6"><div class="stat-item"><div class="stat-label">总工作小时</div><div class="stat-value">{{ statisticsData.total_work_hours }}</div></div></el-col>
            <el-col :span="6"><div class="stat-item"><div class="stat-label">总加班小时</div><div class="stat-value">{{ statisticsData.total_overtime_hours }}</div></div></el-col>
            <el-col :span="6"><div class="stat-item"><div class="stat-label">平均每日工时</div><div class="stat-value">{{ statisticsData.avg_daily_hours }}</div></div></el-col>
            <el-col :span="6"><div class="stat-item"><div class="stat-label">异常次数</div><div class="stat-value" style="color: #f56c6c">{{ statisticsData.abnormal_count }}</div></div></el-col>
          </el-row>
          <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="8"><div class="stat-item"><div class="stat-label">迟到次数</div><div class="stat-value" style="color: #e6a23c">{{ statisticsData.late_count }}</div></div></el-col>
            <el-col :span="8"><div class="stat-item"><div class="stat-label">早退次数</div><div class="stat-value" style="color: #e6a23c">{{ statisticsData.early_leave_count }}</div></div></el-col>
          </el-row>
        </el-card>

        <el-card shadow="hover" style="margin-top: 20px" v-if="statisticsData.abnormal_analysis && statisticsData.abnormal_analysis.total > 0">
          <div slot="header">
            <span style="font-weight: bold; font-size: 16px">异常分析</span>
          </div>
          <el-table :data="abnormalAnalysisList" border>
            <el-table-column prop="type" label="异常类型" width="200" />
            <el-table-column prop="count" label="次数" />
          </el-table>
        </el-card>

        <el-card shadow="hover" style="margin-top: 20px">
          <div slot="header">
            <span style="font-weight: bold; font-size: 16px">详细记录</span>
            <span style="float: right; color: #909399">共 {{ statisticsData.records ? statisticsData.records.length : 0 }} 条</span>
          </div>
          <el-table :data="statisticsData.records" border max-height="400">
            <el-table-column prop="work_date" label="日期" width="120" />
            <el-table-column prop="check_in" label="上班打卡" width="160" />
            <el-table-column prop="check_out" label="下班打卡" width="160" />
            <el-table-column prop="work_hours" label="工时" width="100" />
            <el-table-column prop="overtime_hours" label="加班" width="100" />
            <el-table-column prop="abnormal" label="异常说明" min-width="200">
              <template slot-scope="scope">
                <span v-if="scope.row.abnormal" style="color: #f56c6c">{{ scope.row.abnormal }}</span>
                <span v-else style="color: #909399">-</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
      <div v-else style="text-align: center; padding: 40px; color: #909399">请选择员工工号和月份后查询统计</div>
    </el-dialog>

    <el-dialog title="导入考勤记录" :visible.sync="importDialogVisible" width="50%" @close="importDialogClosed">
      <div style="margin-bottom: 20px">
        <el-alert title="导入说明" type="info" :closable="false" show-icon>
          <div slot="description">
            <p>1. 请使用系统模板并按列填写数据。</p>
            <p>2. 必填列：工号、日期。</p>
            <p>3. 工号必须已在系统中存在。</p>
            <p>4. 同员工同日期记录会执行更新。</p>
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
        <div class="el-upload__tip" slot="tip">只能上传 xlsx/xls 文件，且不超过 10MB</div>
      </el-upload>

      <div v-if="importResult" style="margin-top: 20px">
        <el-alert :title="importResult.message" :type="importResult.fail_count > 0 ? 'warning' : 'success'" :closable="false" show-icon>
          <div slot="description">
            <p>成功: {{ importResult.success_count }} 条</p>
            <p>失败: {{ importResult.fail_count }} 条</p>
            <p>总计: {{ importResult.total }} 条</p>
            <div v-if="importResult.errors && importResult.errors.length > 0" style="margin-top: 10px">
              <p style="font-weight: bold">错误详情：</p>
              <ul style="margin: 5px 0; padding-left: 20px">
                <li v-for="(error, index) in importResult.errors" :key="index">第 {{ error.row }} 行: {{ error.error }}</li>
              </ul>
            </div>
          </div>
        </el-alert>
      </div>

      <span slot="footer" class="dialog-footer">
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleImport" :loading="importing">开始导入</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { exportToExcel } from '@/utils/excelExport'

export default {
  data() {
    return {
      searchQuery: {
        employee_id: '',
        work_date: '',
      },
      attendanceList: [],
      attendanceListShow: [],
      total: 0,
      currentPage: 1,
      pageSize: 10,
      loading: false,
      exporting: false,
      submitting: false,
      editDialogVisible: false,
      addDialogVisible: false,
      statisticsDialogVisible: false,
      statisticsForm: {
        employee_id: '',
        period: '',
      },
      statisticsData: null,
      statisticsLoading: false,
      detectingAbnormal: false,
      importDialogVisible: false,
      importFileList: [],
      importFile: null,
      importing: false,
      importResult: null,
      operationFeedback: null,
      addForm: {
        employee: '',
        work_date: '',
        check_in: '',
        check_out: '',
        work_hours: null,
        overtime_hours: null,
        abnormal: '',
      },
      addFormRules: {
        employee: [{ required: true, message: '请输入工号', trigger: 'blur' }],
        work_date: [{ required: true, message: '请选择日期', trigger: 'change' }],
      },
      editForm: {
        id: null,
        employee_id: '',
        employee_name: '',
        work_date: '',
        check_in: '',
        check_out: '',
        work_hours: null,
        overtime_hours: null,
        abnormal: '',
      },
      editFormRules: {
        work_date: [{ required: true, message: '请选择日期', trigger: 'change' }],
      },
    }
  },
  computed: {
    abnormalAnalysisList() {
      if (!this.statisticsData || !this.statisticsData.abnormal_analysis || !this.statisticsData.abnormal_analysis.by_type) {
        return []
      }
      const byType = this.statisticsData.abnormal_analysis.by_type
      return Object.keys(byType).map((type) => ({ type, count: byType[type] }))
    },
    abnormalCount() {
      return this.attendanceList.filter((item) => item && item.abnormal).length
    },
    currentPageHours() {
      const totalHours = this.attendanceListShow.reduce((sum, item) => sum + Number(item.work_hours || 0), 0)
      return totalHours ? totalHours.toFixed(1) : '0.0'
    },
  },
  created() {
    this.getAttendanceList(false)
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
    refreshPageData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.attendanceListShow = this.attendanceList.slice(start, end)
    },
    async getAttendanceList(search = false) {
      this.loading = true
      try {
        const params = {}
        if (search) {
          if (this.searchQuery.employee_id) params.employee_id = this.searchQuery.employee_id
          if (this.searchQuery.work_date) params.work_date = this.searchQuery.work_date
        } else {
          this.searchQuery.employee_id = ''
          this.searchQuery.work_date = ''
        }

        const { data: res } = await this.$http.get('/api/attendance/', { params })
        const list = Array.isArray(res) ? res : (Array.isArray(res.results) ? res.results : [])

        this.attendanceList = list
        this.total = list.length
        this.currentPage = 1
        this.refreshPageData()
      } catch (error) {
        console.error('获取考勤列表失败:', error)
        this.$message.error(this.getErrorMessage(error, '获取考勤列表失败'))
      } finally {
        this.loading = false
      }
    },
    addDialogClosed() {
      this.$refs.addFormRef && this.$refs.addFormRef.resetFields()
    },
    addAttendance() {
      if (this.submitting) {
        return
      }
      this.$refs.addFormRef.validate(async (valid) => {
        if (!valid) return
        this.submitting = true
        try {
          await this.$http.post('/api/attendance/', {
            employee: this.addForm.employee,
            work_date: this.addForm.work_date,
            check_in: this.addForm.check_in || null,
            check_out: this.addForm.check_out || null,
            work_hours: this.addForm.work_hours,
            overtime_hours: this.addForm.overtime_hours,
            abnormal: this.addForm.abnormal || '',
          })
          this.$message.success('考勤记录保存成功')
          this.addDialogVisible = false
          this.getAttendanceList(false)
        } catch (error) {
          console.error('新增考勤失败:', error)
          this.$message.error(this.getErrorMessage(error, '新增考勤记录失败'))
        } finally {
          this.submitting = false
        }
      })
    },
    showEditDialog(row) {
      this.editDialogVisible = true
      this.editForm.id = row.id
      this.editForm.employee_id = row.employee_id
      this.editForm.employee_name = row.employee_name
      this.editForm.work_date = row.work_date
      this.editForm.check_in = row.check_in
      this.editForm.check_out = row.check_out
      this.editForm.work_hours = row.work_hours
      this.editForm.overtime_hours = row.overtime_hours
      this.editForm.abnormal = row.abnormal
    },
    editDialogClosed() {
      this.$refs.editFormRef && this.$refs.editFormRef.resetFields()
    },
    editAttendance() {
      if (this.submitting) {
        return
      }
      this.$refs.editFormRef.validate(async (valid) => {
        if (!valid) return
        this.submitting = true
        try {
          await this.$http.patch(`/api/attendance/${this.editForm.id}/`, {
            work_date: this.editForm.work_date,
            check_in: this.editForm.check_in || null,
            check_out: this.editForm.check_out || null,
            work_hours: this.editForm.work_hours,
            overtime_hours: this.editForm.overtime_hours,
            abnormal: this.editForm.abnormal || '',
          })
          this.$message.success('考勤记录保存成功')
          this.editDialogVisible = false
          this.getAttendanceList(false)
        } catch (error) {
          console.error('修改考勤失败:', error)
          this.$message.error(this.getErrorMessage(error, '更新考勤记录失败'))
        } finally {
          this.submitting = false
        }
      })
    },
    deleteAttendance(row) {
      this.$confirm('此操作将永久删除该考勤记录，是否继续？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(async () => {
          try {
            await this.$http.delete(`/api/attendance/${row.id}/`)
            this.$message.success('删除考勤记录成功')
            this.getAttendanceList(false)
          } catch (error) {
            console.error('删除考勤失败:', error)
            this.$message.error(this.getErrorMessage(error, '删除考勤记录失败'))
          }
        })
        .catch(() => {
          this.$message.info('已取消删除')
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
    getErrorMessage(error, defaultMsg) {
      if (!error.response || !error.response.data) {
        return `${defaultMsg}，请检查网络连接`
      }
      const data = error.response.data
      if (data.detail) {
        if (typeof data.detail === 'string') return data.detail
        if (Array.isArray(data.detail)) return data.detail[0]
      }

      const fieldErrors = []
      Object.keys(data).forEach((key) => {
        if (Array.isArray(data[key]) && data[key].length > 0) {
          fieldErrors.push(`${this.getFieldName(key)}: ${data[key][0]}`)
        } else if (typeof data[key] === 'string') {
          fieldErrors.push(`${this.getFieldName(key)}: ${data[key]}`)
        }
      })

      if (fieldErrors.length > 0) return fieldErrors.join('；')
      if (data.non_field_errors) return Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : data.non_field_errors
      return defaultMsg
    },
    getFieldName(field) {
      const fieldMap = {
        employee: '工号',
        work_date: '日期',
        check_in: '上班打卡时间',
        check_out: '下班打卡时间',
        work_hours: '工时',
        overtime_hours: '加班时长',
        abnormal: '异常说明',
      }
      return fieldMap[field] || field
    },
    async getStatistics() {
      if (!this.statisticsForm.employee_id || !this.statisticsForm.period) {
        this.$message.warning('请填写员工工号并选择月份')
        return
      }

      this.statisticsLoading = true
      try {
        const { data: res } = await this.$http.get('/api/attendance/statistics/', {
          params: {
            employee_id: this.statisticsForm.employee_id,
            period: this.statisticsForm.period,
          },
        })

        if (res.success && res.data) {
          this.statisticsData = res.data
          this.$message.success('统计查询成功')
        } else {
          this.$message.error(res.error || '获取统计信息失败')
        }
      } catch (error) {
        console.error('获取考勤统计失败:', error)
        const errorMsg = this.getErrorMessage(error, '获取考勤统计失败')
        const backendError = error && error.response && error.response.data ? error.response.data.error : ''
        this.$message.error(backendError || errorMsg)
      } finally {
        this.statisticsLoading = false
      }
    },
    async autoDetectAbnormal() {
      if (!this.statisticsForm.employee_id || !this.statisticsForm.period) {
        this.$message.warning('请填写员工工号并选择月份')
        return
      }

      this.detectingAbnormal = true
      try {
        const { data: res } = await this.$http.post('/api/attendance/auto-detect-abnormal/', {
          employee_id: this.statisticsForm.employee_id,
          period: this.statisticsForm.period,
        })

        if (res.success) {
          this.$message.success(res.message || '自动识别异常完成')
          if (this.statisticsData) {
            this.getStatistics()
          }
        } else {
          this.$message.error(res.error || '自动识别异常失败')
        }
      } catch (error) {
        console.error('自动识别异常失败:', error)
        const errorMsg = this.getErrorMessage(error, '自动识别异常失败')
        const backendError = error && error.response && error.response.data ? error.response.data.error : ''
        this.$message.error(backendError || errorMsg)
      } finally {
        this.detectingAbnormal = false
      }
    },
    statisticsDialogClosed() {
      this.statisticsData = null
      this.statisticsForm.employee_id = ''
      this.statisticsForm.period = ''
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
      this.$message.info('正在解析考勤 Excel 文件，请稍候...')
      try {
        const { data: res } = await this.$http.post('/api/import/attendance/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })

        if (res.success) {
          this.importResult = res
          const successCount = Number(res.success_count)
          const failCount = Number(res.fail_count)
          if (Number.isFinite(successCount) && Number.isFinite(failCount)) {
            this.$message.success(`考勤导入完成：成功 ${successCount} 条，失败 ${failCount} 条`)
            this.setOperationFeedback({
              module: '考勤管理',
              action: 'Excel 导入',
              status: 'success',
              result: '导入完成',
              count: successCount,
              countText: `成功 ${successCount} 条，失败 ${failCount} 条`,
              description: '考勤 Excel 导入请求已完成，页面数据已刷新',
            })
          } else {
            this.$message.success(res.message || '考勤导入完成')
            this.setOperationFeedback({
              module: '考勤管理',
              action: 'Excel 导入',
              status: 'success',
              result: '导入完成',
              description: '考勤 Excel 导入请求已完成，页面数据已刷新',
            })
          }
          this.getAttendanceList(false)
        } else {
          const reason = res.error || res.message || '考勤导入失败'
          this.$message.error(reason)
          this.setOperationFeedback({
            module: '考勤管理',
            action: 'Excel 导入',
            status: 'error',
            result: '导入失败',
            reason,
            description: '本次操作未完成，请根据错误提示检查数据或网络状态',
          })
        }
      } catch (error) {
        console.error('导入失败:', error)
        let errorMsg = '导入失败'
        if (error && error.response && error.response.data) {
          errorMsg = error.response.data.error || error.response.data.detail || errorMsg
        }
        this.$message.error(errorMsg)
        this.setOperationFeedback({
          module: '考勤管理',
          action: 'Excel 导入',
          status: 'error',
          result: '导入失败',
          reason: errorMsg,
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
    async exportToExcel() {
      if (!this.attendanceList || this.attendanceList.length === 0) {
        this.$message.warning('没有数据可导出')
        return
      }

      const columns = [
        { key: 'employee_id', label: '工号' },
        { key: 'employee_name', label: '姓名' },
        { key: 'work_date', label: '日期' },
        { key: 'check_in', label: '上班打卡时间' },
        { key: 'check_out', label: '下班打卡时间' },
        { key: 'work_hours', label: '工时' },
        { key: 'overtime_hours', label: '加班时长' },
        { key: 'abnormal', label: '异常说明' },
      ]

      this.exporting = true
      this.$message.info('正在生成考勤数据导出文件，请稍候...')
      try {
        const result = await exportToExcel(this.attendanceList, columns, '考勤记录')
        if (typeof result.count === 'number') {
          this.$message.success(`考勤数据导出成功，共导出 ${result.count} 条记录`)
        } else {
          this.$message.success('考勤数据导出成功，文件已生成')
        }
        this.setOperationFeedback({
          module: '考勤管理',
          action: 'Excel 导出',
          status: 'success',
          result: '导出成功',
          count: typeof result.count === 'number' ? result.count : null,
          filename: result.filename,
          description: '考勤数据导出功能返回成功反馈，浏览器已生成下载文件',
        })
      } catch (error) {
        const reason = error.message || '考勤数据导出失败'
        this.$message.error(reason)
        this.setOperationFeedback({
          module: '考勤管理',
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

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
}

/deep/ .action-buttons .el-button {
  box-shadow: none;
}

.text {
  display: flex;
  justify-content: center;
  align-items: center;
}

.stat-item {
  text-align: center;
  padding: 14px 10px;
  border-radius: 12px;
  border: 1px solid rgba(23, 80, 158, 0.1);
  background: linear-gradient(135deg, rgba(245, 251, 255, 0.94), rgba(250, 253, 255, 0.92));

  .stat-label {
    font-size: 13px;
    color: #617ea3;
    margin-bottom: 8px;
  }

  .stat-value {
    font-size: 24px;
    font-weight: 700;
    color: #1b4f90;
    line-height: 1.1;
  }
}

/deep/ .el-dialog {
  border-radius: 16px;
  overflow: hidden;
}

/deep/ .el-dialog__header {
  background: #f8fafc;
  border-bottom: 1px solid #e7edf5;
}

/deep/ .el-dialog__body {
  padding: 18px 20px;
}

/deep/ .el-dialog__footer {
  border-top: 1px solid #e7edf5;
  background: #f8fafc;
}
</style>


