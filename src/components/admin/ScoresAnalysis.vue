<template>
  <div class="biz-page">
    <section class="biz-page__hero">
      <div class="biz-page__hero-copy">
        <p class="biz-page__eyebrow">Payroll Operation</p>
        <h1 class="biz-page__title">薪酬核算</h1>
        <p class="biz-page__description">
          统一管理员工月度薪酬，支持按工号和月份筛选、自动计算、批量生成结果以及导出核算数据。
        </p>
        <div class="biz-page__meta">
          <span class="biz-page__badge">薪酬记录 {{ total }} 条</span>
          <span class="biz-page__badge">当前页 {{ payrollListShow.length }} 条</span>
        </div>
      </div>
      <div class="biz-page__hero-side">
        <div class="biz-page__stat">
          <p class="biz-page__stat-label">已确认记录</p>
          <p class="biz-page__stat-value">{{ confirmedCount }}</p>
        </div>
      </div>
    </section>

    <el-card class="biz-page__panel">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-main">
          <h2 class="biz-page__toolbar-title">薪酬记录列表</h2>
          <p class="biz-page__toolbar-desc">支持自动计算、手动维护和批量导出，适合月度薪酬核算与复核。</p>
        </div>
        <div class="biz-page__toolbar-actions">
          <el-button type="warning" icon="el-icon-cpu" @click="showBatchCalculateDialog">批量自动计算</el-button>
          <el-button type="success" icon="el-icon-download" :loading="exporting" :disabled="exporting" @click="exportToExcel">导出Excel</el-button>
          <el-button type="primary" icon="el-icon-plus" @click="showAddDialog">新增薪酬</el-button>
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
          <el-input
            placeholder="请输入工号"
            v-model="searchQuery.employee_id"
            clearable
            style="width: 200px"
          ></el-input>
        </el-form-item>
        <el-form-item label="月份">
          <el-date-picker
            v-model="searchQuery.period"
            type="month"
            placeholder="选择月份"
            value-format="yyyy-MM"
            style="width: 200px"
          ></el-date-picker>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getPayrollList">查询</el-button>
          <el-button type="default" icon="el-icon-refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <div style="position: relative;">
        <el-table 
          :data="payrollListShow" 
          border 
          stripe 
          style="width: 100%"
          v-show="!loading"
        >
        <el-table-column type="index" label="序号" width="70" align="center"></el-table-column>
        <el-table-column prop="employee_id" label="工号" min-width="110" align="center"></el-table-column>
        <el-table-column prop="employee_name" label="姓名" min-width="110" align="center"></el-table-column>
        <el-table-column prop="period" label="月份" min-width="110" align="center"></el-table-column>
        <el-table-column prop="base_pay" label="基本工资" min-width="115" align="right">
          <template slot-scope="scope">
            <span class="money-text">{{ formatMoney(scope.row.base_pay) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="allowance" label="津贴" min-width="115" align="right">
          <template slot-scope="scope">
            <span class="money-text">{{ formatMoney(scope.row.allowance) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="bonus" label="奖金" min-width="115" align="right">
          <template slot-scope="scope">
            <span class="money-text">{{ formatMoney(scope.row.bonus) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="deduction" label="扣除" min-width="115" align="right">
          <template slot-scope="scope">
            <span class="money-text deduction-text">{{ formatMoney(scope.row.deduction) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="tax" label="个税" min-width="115" align="right">
          <template slot-scope="scope">
            <span class="money-text deduction-text">{{ formatMoney(scope.row.tax) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="social_security" label="社保" min-width="115" align="right">
          <template slot-scope="scope">
            <span class="money-text deduction-text">{{ formatMoney(scope.row.social_security) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="housing_fund" label="公积金" min-width="115" align="right">
          <template slot-scope="scope">
            <span class="money-text deduction-text">{{ formatMoney(scope.row.housing_fund) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="net_pay" label="实发工资" min-width="130" align="right">
          <template slot-scope="scope">
            <span class="net-pay-text">
              {{ formatMoney(scope.row.net_pay) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="100" align="center">
          <template slot-scope="scope">
            <el-tag v-if="scope.row.status === 'DRAFT'" type="info" size="small">草稿</el-tag>
            <el-tag v-else-if="scope.row.status === 'CONFIRMED'" type="success" size="small">已确认</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="110" align="center">
          <template slot-scope="scope">
            <div class="action-buttons">
              <el-tooltip content="编辑" placement="top">
                <el-button
                  type="primary"
                  icon="el-icon-edit"
                  size="mini"
                  circle
                  @click="showEditDialog(scope.row)"
                ></el-button>
              </el-tooltip>
              <el-tooltip content="删除" placement="top">
                <el-button
                  type="danger"
                  icon="el-icon-delete"
                  size="mini"
                  circle
                  @click="deletePayroll(scope.row)"
                ></el-button>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
        <div v-if="loading" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255, 255, 255, 0.9); display: flex; align-items: center; justify-content: center; z-index: 10;">
          <i class="el-icon-loading" style="font-size: 30px; color: #409EFF;"></i>
          <span style="margin-left: 10px; color: #409EFF;">加载中...</span>
        </div>
      </div>
      <div v-if="!loading && !payrollListShow.length" class="biz-page__table-empty">
        <p class="biz-page__table-empty-title">当前没有薪酬记录</p>
        <p class="biz-page__table-empty-desc">可以调整工号或月份筛选，或直接新增一条薪酬记录。</p>
      </div>

      <el-pagination
        class="biz-page__pagination"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[10, 15, 20, 30]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
      >
      </el-pagination>
    </el-card>

    <!-- 新增/编辑薪酬对话框 -->
    <el-dialog
      :title="dialogTitle"
      :visible.sync="dialogVisible"
      width="60%"
      @close="dialogClosed"
    >
      <el-form
        :model="form"
        :rules="formRules"
        ref="formRef"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工号" prop="employee">
              <el-input
                v-model="form.employee"
                placeholder="请输入工号"
                clearable
              ></el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="月份" prop="period">
              <el-date-picker
                v-model="form.period"
                type="month"
                placeholder="选择月份"
                value-format="yyyy-MM"
                style="width: 100%"
              ></el-date-picker>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item>
              <el-button 
                type="warning" 
                icon="el-icon-cpu" 
                @click="autoCalculatePayroll"
                :loading="calculating"
                :disabled="!form.employee || !form.period"
              >
                自动计算薪资
              </el-button>
              <span style="margin-left: 10px; color: #909399; font-size: 12px;">
                根据考勤、加班、请假等数据自动计算薪资
              </span>
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">
          <span style="color: #67C23A; font-weight: bold;">收入项</span>
        </el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="基本工资" prop="base_pay">
              <el-input-number
                v-model="form.base_pay"
                :precision="2"
                :min="0"
                :step="100"
                style="width: 100%"
              ></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="津贴" prop="allowance">
              <el-input-number
                v-model="form.allowance"
                :precision="2"
                :min="0"
                :step="100"
                style="width: 100%"
              ></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="奖金" prop="bonus">
              <el-input-number
                v-model="form.bonus"
                :precision="2"
                :min="0"
                :step="100"
                style="width: 100%"
              ></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">
          <span style="color: #F56C6C; font-weight: bold;">扣除项</span>
        </el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="扣除" prop="deduction">
              <el-input-number
                v-model="form.deduction"
                :precision="2"
                :min="0"
                :step="100"
                style="width: 100%"
              ></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="个税" prop="tax">
              <el-input-number
                v-model="form.tax"
                :precision="2"
                :min="0"
                :step="100"
                style="width: 100%"
              ></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="社保" prop="social_security">
              <el-input-number
                v-model="form.social_security"
                :precision="2"
                :min="0"
                :step="100"
                style="width: 100%"
              ></el-input-number>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="公积金" prop="housing_fund">
              <el-input-number
                v-model="form.housing_fund"
                :precision="2"
                :min="0"
                :step="100"
                style="width: 100%"
              ></el-input-number>
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">
          <span style="color: #409EFF; font-weight: bold;">计算结果</span>
        </el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="实发工资">
              <el-input
                :value="formatMoney(calculateNetPay)"
                readonly
                class="net-pay-input"
              >
                <template slot="prepend">¥</template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="form.status" placeholder="请选择状态" style="width: 100%">
                <el-option label="草稿" value="DRAFT"></el-option>
                <el-option label="已确认" value="CONFIRMED"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" @click="submitForm">确 定</el-button>
      </span>
    </el-dialog>

    <!-- 批量自动计算对话框 -->
    <el-dialog
      title="批量自动计算薪资"
      :visible.sync="batchCalculateDialogVisible"
      width="50%"
    >
      <el-form label-width="120px">
        <el-form-item label="月份" required>
          <el-date-picker
            v-model="batchCalculatePeriod"
            type="month"
            placeholder="选择月份"
            value-format="yyyy-MM"
            style="width: 100%"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="员工工号">
          <el-input
            v-model="batchCalculateEmployeeId"
            placeholder="请输入要计算的员工工号"
            clearable
          ></el-input>
          <div style="margin-top: 5px; color: #909399; font-size: 12px;">
            提示：输入员工工号后，系统将自动计算该员工指定月份的薪资
          </div>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="batchCalculateDialogVisible = false">取 消</el-button>
        <el-button type="warning" @click="batchCalculatePayroll" :loading="batchCalculating">开始计算</el-button>
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
        period: '',
      },
      payrollList: [], // 所有薪酬数据
      payrollListShow: [], // 当前页显示的薪酬数据
      loading: false, // 加载状态
      exporting: false, // 导出状态
      operationFeedback: null,
      currentPage: 1, // 当前页码
      pageSize: 15, // 每页显示数量
      total: 0, // 总记录数
      dialogVisible: false,
      dialogTitle: '新增薪酬',
      isEdit: false,
      calculating: false, // 自动计算中
      batchCalculateDialogVisible: false, // 批量计算对话框
      batchCalculating: false, // 批量计算中
      batchCalculatePeriod: '', // 批量计算的月份
      batchCalculateEmployeeId: '', // 批量计算的员工工号
      currentId: null, // 当前编辑的记录ID
      form: {
        employee: '',
        period: '',
        base_pay: null,
        allowance: null,
        bonus: null,
        deduction: null,
        tax: null,
        social_security: null,
        housing_fund: null,
        net_pay: 0,
        status: 'DRAFT',
      },
      formRules: {
        employee: [
          { required: true, message: '请输入工号', trigger: 'blur' },
        ],
        period: [
          { required: true, message: '请选择月份', trigger: 'change' },
        ],
      },
    }
  },
  computed: {
    confirmedCount() {
      return this.payrollList.filter((item) => item && item.status === 'CONFIRMED').length
    },
    calculateNetPay() {
      const income = (this.form.base_pay || 0) + (this.form.allowance || 0) + (this.form.bonus || 0)
      const deduction = (this.form.deduction || 0) + (this.form.tax || 0) + (this.form.social_security || 0) + (this.form.housing_fund || 0)
      return income - deduction
    },
  },
  created() {
    this.getPayrollList()
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
    // 格式化金额
    formatMoney(value) {
      if (value === null || value === undefined) return '0.00'
      return Number(value).toFixed(2)
    },
    // 获取薪酬列表
    async getPayrollList() {
      this.loading = true
      try {
        const params = {}
        if (this.searchQuery.employee_id) {
          params.employee_id = this.searchQuery.employee_id
        }
        if (this.searchQuery.period) {
          params.period = this.searchQuery.period
        }
        const { data: res } = await this.$http.get('/api/payroll/', { params })
        if (res && Array.isArray(res)) {
          this.payrollList = res
          this.total = res.length
          this.updatePayrollListShow()
        } else {
          this.$message.error('获取薪酬列表失败')
          this.payrollList = []
          this.payrollListShow = []
          this.total = 0
        }
      } catch (error) {
        console.error('获取薪酬列表失败:', error)
        const errorMsg = this.getErrorMessage(error, '获取薪酬列表失败')
        this.$message.error(errorMsg)
      } finally {
        this.loading = false
      }
    },
    // 重置搜索
    resetSearch() {
      this.searchQuery = {
        employee_id: '',
        period: '',
      }
      this.currentPage = 1 // 重置到第一页
      this.getPayrollList()
    },
    // 显示新增对话框
    showAddDialog() {
      this.dialogTitle = '新增薪酬'
      this.isEdit = false
      this.dialogVisible = true
    },
    // 显示编辑对话框
    showEditDialog(row) {
      this.dialogTitle = '编辑薪酬'
      this.isEdit = true
      this.form = {
        employee: row.employee_id,
        period: row.period,
        base_pay: row.base_pay != null ? parseFloat(row.base_pay) : null,
        allowance: row.allowance != null ? parseFloat(row.allowance) : null,
        bonus: row.bonus != null ? parseFloat(row.bonus) : null,
        deduction: row.deduction != null ? parseFloat(row.deduction) : null,
        tax: row.tax != null ? parseFloat(row.tax) : null,
        social_security: row.social_security != null ? parseFloat(row.social_security) : null,
        housing_fund: row.housing_fund != null ? parseFloat(row.housing_fund) : null,
        net_pay: parseFloat(row.net_pay) || 0,
        status: row.status,
      }
      this.currentId = row.id
      this.dialogVisible = true
    },
    // 对话框关闭
    dialogClosed() {
      this.$refs.formRef.resetFields()
      this.form = {
        employee: '',
        period: '',
        base_pay: null,
        allowance: null,
        bonus: null,
        deduction: null,
        tax: null,
        social_security: null,
        housing_fund: null,
        net_pay: 0,
        status: 'DRAFT',
      }
      this.isEdit = false
      this.currentId = null
    },
    // 提交表单
    submitForm() {
      this.$refs.formRef.validate(async (valid) => {
        if (!valid) return
        // 计算实发工资
        this.form.net_pay = this.calculateNetPay
        // 准备提交数据，将 null 转换为 0
        const submitData = {
          ...this.form,
          base_pay: this.form.base_pay || 0,
          allowance: this.form.allowance || 0,
          bonus: this.form.bonus || 0,
          deduction: this.form.deduction || 0,
          tax: this.form.tax || 0,
          social_security: this.form.social_security || 0,
          housing_fund: this.form.housing_fund || 0,
        }
        try {
          if (this.isEdit) {
            // 编辑
            await this.$http.patch(`/api/payroll/${this.currentId}/`, submitData)
          } else {
            // 新增
            await this.$http.post('/api/payroll/', submitData)
          }
          this.$message.success(this.isEdit ? '更新薪酬记录成功！' : '新增薪酬记录成功！')
          this.dialogVisible = false
          this.getPayrollList()
        } catch (error) {
          console.error('提交失败:', error)
          const errorMsg = this.getErrorMessage(error, this.isEdit ? '更新薪酬记录失败' : '新增薪酬记录失败')
          this.$message.error(errorMsg)
        }
      })
    },
    // 删除薪酬
    deletePayroll(row) {
      this.$confirm('此操作将永久删除该薪酬记录, 是否继续?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(async () => {
          try {
            await this.$http.delete(`/api/payroll/${row.id}/`)
            this.$message.success('删除薪酬记录成功！')
            this.getPayrollList()
          } catch (error) {
            console.error('删除失败:', error)
            const errorMsg = this.getErrorMessage(error, '删除薪酬记录失败')
            this.$message.error(errorMsg)
          }
        })
        .catch(() => {
          this.$message.info('已取消删除')
        })
    },
    // 统一错误消息处理
    getErrorMessage(error, defaultMsg) {
      if (!error.response || !error.response.data) {
        return defaultMsg + '，请检查网络连接'
      }
      const data = error.response.data
      
      // 处理 detail 字段（DRF 标准错误格式）
      if (data.detail) {
        return typeof data.detail === 'string' ? data.detail : (Array.isArray(data.detail) ? data.detail[0] : JSON.stringify(data.detail))
      }
      
      // 处理字段验证错误
      const fieldErrors = []
      for (const key in data) {
        if (data.hasOwnProperty(key) && Array.isArray(data[key]) && data[key].length > 0) {
          fieldErrors.push(`${this.getFieldName(key)}: ${data[key][0]}`)
        } else if (data.hasOwnProperty(key) && typeof data[key] === 'string') {
          fieldErrors.push(`${this.getFieldName(key)}: ${data[key]}`)
        }
      }
      
      if (fieldErrors.length > 0) {
        return fieldErrors.join('；')
      }
      
      // 处理非字段错误
      if (data.non_field_errors) {
        const nonFieldError = Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : data.non_field_errors
        return nonFieldError
      }
      
      // 如果是字符串，直接返回
      if (typeof data === 'string') {
        return data
      }
      
      return defaultMsg
    },
    // 字段名称映射
    getFieldName(field) {
      const fieldMap = {
        employee: '工号',
        period: '月份',
        base_pay: '基本工资',
        allowance: '津贴',
        bonus: '奖金',
        deduction: '扣除',
        tax: '个税',
        social_security: '社保',
        housing_fund: '公积金',
        net_pay: '实发工资',
        status: '状态',
      }
      return fieldMap[field] || field
    },
    // 导出Excel
    async exportToExcel() {
      if (!this.payrollList || this.payrollList.length === 0) {
        this.$message.warning('没有数据可导出')
        return
      }

      const columns = [
        { key: 'employee_id', label: '工号' },
        { key: 'employee_name', label: '姓名' },
        { key: 'period', label: '月份' },
        { key: 'base_pay', label: '基本工资' },
        { key: 'allowance', label: '津贴' },
        { key: 'bonus', label: '奖金' },
        { key: 'overtime_pay', label: '加班费' },
        { key: 'deduction', label: '扣除' },
        { key: 'net_pay', label: '实发工资' },
      ]

      this.exporting = true
      this.$message.info('正在生成薪资数据导出文件，请稍候...')
      try {
        const result = await exportToExcel(this.payrollList, columns, '薪酬记录')
        if (typeof result.count === 'number') {
          this.$message.success(`薪资数据导出成功，共导出 ${result.count} 条记录`)
        } else {
          this.$message.success('薪资数据导出成功，文件已生成')
        }
        this.setOperationFeedback({
          module: '薪资管理',
          action: 'Excel 导出',
          status: 'success',
          result: '导出成功',
          count: typeof result.count === 'number' ? result.count : null,
          filename: result.filename,
          description: '薪资数据导出请求已完成，浏览器已生成下载文件',
        })
      } catch (error) {
        const reason = error.message || '薪资数据导出失败'
        this.$message.error(reason)
        this.setOperationFeedback({
          module: '薪资管理',
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
    // 更新显示的薪酬列表（分页）
    updatePayrollListShow() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.payrollListShow = this.payrollList.slice(start, end)
    },
    // 分页大小改变
    handleSizeChange(pageSize) {
      this.pageSize = pageSize
      this.currentPage = 1 // 重置到第一页
      this.updatePayrollListShow()
    },
    // 当前页改变
    handleCurrentChange(currentPage) {
      this.currentPage = currentPage
      this.updatePayrollListShow()
    },
    // 自动计算薪资（在表单中）
    async autoCalculatePayroll() {
      if (!this.form.employee || !this.form.period) {
        this.$message.warning('请先输入工号和选择月份')
        return
      }

      this.calculating = true
      try {
        const { data: res } = await this.$http.post('/api/payroll/auto-generate/', {
          employee_id: this.form.employee,
          period: this.form.period,
          bonus: this.form.bonus || 0,
          other_deduction: 0
        })

        if (res.success && res.data) {
          // 将计算结果填充到表单
          this.form.base_pay = parseFloat(res.data.base_pay) || 0
          this.form.allowance = parseFloat(res.data.allowance) || 0
          this.form.bonus = parseFloat(res.data.bonus) || 0
          this.form.deduction = parseFloat(res.data.deduction) || 0
          this.form.tax = parseFloat(res.data.tax) || 0
          this.form.social_security = parseFloat(res.data.social_security) || 0
          this.form.housing_fund = parseFloat(res.data.housing_fund) || 0
          this.form.net_pay = parseFloat(res.data.net_pay) || 0
          this.form.status = res.data.status || 'DRAFT'

          this.$message.success('薪资计算成功！计算结果已填充到表单，您可以进行调整后保存。')
          
          // 如果是编辑模式，需要更新记录ID
          if (res.data.id) {
            this.currentId = res.data.id
            this.isEdit = true
            this.dialogTitle = '编辑薪酬'
          }
        } else {
          this.$message.error(res.error || '计算薪资失败')
        }
      } catch (error) {
        console.error('自动计算薪资失败:', error)
        console.error('错误详情:', error.response && error.response.data)
        let errorMsg = this.getErrorMessage(error, '自动计算薪资失败')
        // 如果有详细错误信息，显示出来
        if (error.response && error.response.data && error.response.data.error) {
          errorMsg = error.response.data.error
        }
        if (error.response && error.response.data && error.response.data.detail) {
          console.error('详细错误堆栈:', error.response.data.detail)
          errorMsg += `\n详细错误：${error.response.data.detail.substring(0, 200)}...`
        }
        this.$message.error(errorMsg)
      } finally {
        this.calculating = false
      }
    },
    // 显示批量计算对话框
    showBatchCalculateDialog() {
      this.batchCalculateDialogVisible = true
      this.batchCalculatePeriod = ''
      this.batchCalculateEmployeeId = ''
    },
    // 批量自动计算薪资
    async batchCalculatePayroll() {
      if (!this.batchCalculatePeriod) {
        this.$message.warning('请选择月份')
        return
      }

      if (!this.batchCalculateEmployeeId) {
        this.$message.warning('请输入员工工号')
        return
      }

      this.batchCalculating = true
      try {
        const { data: res } = await this.$http.post('/api/payroll/auto-generate/', {
          employee_id: this.batchCalculateEmployeeId,
          period: this.batchCalculatePeriod,
          bonus: 0,
          other_deduction: 0
        })

        if (res.success) {
          this.$message.success('薪资批量计算完成，数据已刷新')
          this.setOperationFeedback({
            module: '薪资管理',
            action: '批量计算',
            status: 'success',
            result: '计算完成',
            description: '薪资批量计算请求已完成，页面数据已刷新',
          })
          this.batchCalculateDialogVisible = false
          this.getPayrollList()
        } else {
          const reason = res.error || '计算薪资失败'
          this.$message.error(reason)
          this.setOperationFeedback({
            module: '薪资管理',
            action: '批量计算',
            status: 'error',
            result: '计算失败',
            reason,
            description: '本次操作未完成，请根据错误提示检查数据或网络状态',
          })
        }
      } catch (error) {
        console.error('批量计算薪资失败:', error)
        console.error('错误详情:', error.response && error.response.data)
        let errorMsg = this.getErrorMessage(error, '批量计算薪资失败')
        // 如果有详细错误信息，显示出来
        if (error.response && error.response.data && error.response.data.error) {
          errorMsg = error.response.data.error
        }
        if (error.response && error.response.data && error.response.data.detail) {
          console.error('详细错误堆栈:', error.response.data.detail)
          errorMsg += `\n详细错误：${error.response.data.detail.substring(0, 200)}...`
        }
        this.$message.error(errorMsg)
        this.setOperationFeedback({
          module: '薪资管理',
          action: '批量计算',
          status: 'error',
          result: '计算失败',
          reason: errorMsg,
          description: '本次操作未完成，请根据错误提示检查数据或网络状态',
        })
      } finally {
        this.batchCalculating = false
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
  align-items: center;
  gap: 8px;
}
.money-text {
  font-family: 'Arial', 'Microsoft YaHei', sans-serif;
  color: #606266;
}
.deduction-text {
  color: #f56c6c;
}
.net-pay-text {
  color: #409EFF;
  font-weight: bold;
  font-size: 14px;
  font-family: 'Arial', 'Microsoft YaHei', sans-serif;
}
.net-pay-input {
  /deep/ .el-input__inner {
    color: #409EFF;
    font-weight: bold;
    font-size: 16px;
    background-color: #f0f9ff;
  }
}
</style>
