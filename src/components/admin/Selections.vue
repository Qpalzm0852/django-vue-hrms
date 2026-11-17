<template>
  <div class="biz-page">
    <section class="biz-page__hero">
      <div class="biz-page__hero-copy">
        <p class="biz-page__eyebrow">Leave Approval</p>
        <h1 class="biz-page__title">请假审批</h1>
        <p class="biz-page__description">
          统一管理员工请假审批流程，支持按工号和状态筛选、直接审批通过或拒绝，并维护历史请假记录。
        </p>
        <div class="biz-page__meta">
          <span class="biz-page__badge">请假记录 {{ total }} 条</span>
          <span class="biz-page__badge">待审批 {{ pendingCount }} 条</span>
        </div>
      </div>
      <div class="biz-page__hero-side">
        <div class="biz-page__stat">
          <p class="biz-page__stat-label">当前页时长</p>
          <p class="biz-page__stat-value">{{ currentPageHours }}</p>
        </div>
      </div>
    </section>

    <el-card class="biz-page__panel">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-main">
          <h2 class="biz-page__toolbar-title">请假记录列表</h2>
          <p class="biz-page__toolbar-desc">支持审批、编辑、删除，以及按条件检索和导出请假记录。</p>
        </div>
        <div class="biz-page__toolbar-actions">
          <el-button type="success" icon="el-icon-download" :loading="exporting" :disabled="exporting" @click="exportToExcel">导出Excel</el-button>
          <el-button type="primary" icon="el-icon-plus" @click="showAddDialog">新增请假</el-button>
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
        <el-form-item label="状态">
          <el-select v-model="searchQuery.status" placeholder="请选择状态" clearable style="width: 150px">
            <el-option label="待审批" value="PENDING" />
            <el-option label="已通过" value="APPROVED" />
            <el-option label="已拒绝" value="REJECTED" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getLeaveList">查询</el-button>
          <el-button type="default" icon="el-icon-refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="leaveListShow" border stripe style="width: 100%">
        <el-table-column type="index" label="序号" width="70" align="center" />
        <el-table-column prop="employee_id" label="工号" width="110" align="center" />
        <el-table-column prop="employee_name" label="姓名" width="110" align="center" />
        <el-table-column prop="type" label="请假类型" width="110" align="center" />
        <el-table-column prop="start_time" label="开始时间" width="170" align="center" />
        <el-table-column prop="end_time" label="结束时间" width="170" align="center" />
        <el-table-column prop="hours" label="时长(小时)" width="110" align="center">
          <template slot-scope="scope">{{ scope.row.hours || '-' }}</template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" min-width="150" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template slot-scope="scope">
            <el-tag v-if="scope.row.status === 'PENDING'" type="warning" size="small">待审批</el-tag>
            <el-tag v-else-if="scope.row.status === 'APPROVED'" type="success" size="small">已通过</el-tag>
            <el-tag v-else-if="scope.row.status === 'REJECTED'" type="danger" size="small">已拒绝</el-tag>
            <el-tag v-else size="small">{{ scope.row.status || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="approver_name" label="审批人" width="110" align="center">
          <template slot-scope="scope">{{ scope.row.approver_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right" align="center">
          <template slot-scope="scope">
            <div class="action-buttons">
              <template v-if="scope.row.status === 'PENDING'">
                <el-tooltip content="通过" placement="top">
                  <el-button type="success" icon="el-icon-check" size="mini" circle :loading="approvingId === scope.row.id" :disabled="approvingId !== null" @click="approveLeave(scope.row)" />
                </el-tooltip>
                <el-tooltip content="拒绝" placement="top">
                  <el-button type="danger" icon="el-icon-close" size="mini" circle :loading="approvingId === scope.row.id" :disabled="approvingId !== null" @click="rejectLeave(scope.row)" />
                </el-tooltip>
              </template>
              <el-tooltip content="编辑" placement="top">
                <el-button type="primary" icon="el-icon-edit" size="mini" circle @click="showEditDialog(scope.row)" />
              </el-tooltip>
              <el-tooltip content="删除" placement="top">
                <el-button type="danger" icon="el-icon-delete" size="mini" circle @click="deleteLeave(scope.row)" />
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !leaveListShow.length" class="biz-page__table-empty">
        <p class="biz-page__table-empty-title">当前没有请假记录</p>
        <p class="biz-page__table-empty-desc">可以调整筛选条件，或直接新增请假记录。</p>
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

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="60%" @close="dialogClosed">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工号" prop="employee">
              <el-input v-model="form.employee" placeholder="请输入工号" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="请假类型" prop="type">
              <el-select v-model="form.type" placeholder="请选择请假类型" style="width: 100%" clearable>
                <el-option label="事假" value="事假" />
                <el-option label="病假" value="病假" />
                <el-option label="年假" value="年假" />
                <el-option label="调休" value="调休" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间" prop="start_time">
              <el-date-picker
                v-model="form.start_time"
                type="datetime"
                placeholder="选择开始时间"
                style="width: 100%"
                value-format="yyyy-MM-dd HH:mm:ss"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间" prop="end_time">
              <el-date-picker
                v-model="form.end_time"
                type="datetime"
                placeholder="选择结束时间"
                style="width: 100%"
                value-format="yyyy-MM-dd HH:mm:ss"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="时长(小时)" prop="hours">
              <el-input-number v-model="form.hours" :precision="2" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="原因" prop="reason">
          <el-input type="textarea" v-model="form.reason" placeholder="请输入请假原因" :rows="4" />
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import { exportToExcel as exportLeaveToExcel } from '@/utils/excelExport'
import { getErrorMessage } from '@/utils/errorHandler'

export default {
  computed: {
    pendingCount() {
      return this.leaveList.filter((item) => item && item.status === 'PENDING').length
    },
    currentPageHours() {
      const totalHours = this.leaveListShow.reduce((sum, item) => sum + Number(item.hours || 0), 0)
      return totalHours ? totalHours.toFixed(1) : '0.0'
    },
  },
  data() {
    return {
      searchQuery: {
        employee_id: '',
        status: '',
      },
      leaveList: [],
      leaveListShow: [],
      loading: false,
      exporting: false,
      approvingId: null,
      operationFeedback: null,
      currentPage: 1,
      pageSize: 15,
      total: 0,
      dialogVisible: false,
      dialogTitle: '新增请假',
      isEdit: false,
      currentId: null,
      form: {
        employee: '',
        type: '',
        start_time: '',
        end_time: '',
        hours: null,
        reason: '',
      },
      formRules: {
        employee: [{ required: true, message: '请输入工号', trigger: 'blur' }],
        type: [{ required: true, message: '请选择请假类型', trigger: 'change' }],
        start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
        end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
      },
    }
  },
  created() {
    this.getLeaveList()
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
    async exportToExcel() {
      if (!this.leaveList || this.leaveList.length === 0) {
        this.$message.warning('没有数据可导出')
        return
      }
      const columns = [
        { key: 'employee_id', label: '工号' },
        { key: 'employee_name', label: '姓名' },
        { key: 'type', label: '请假类型' },
        { key: 'start_time', label: '开始时间' },
        { key: 'end_time', label: '结束时间' },
        { key: 'hours', label: '时长(小时)' },
        { key: 'reason', label: '原因' },
        { key: 'status', label: '状态' },
        { key: 'approver_name', label: '审批人' },
      ]
      this.exporting = true
      this.$message.info('正在生成请假数据导出文件，请稍候...')
      try {
        const result = await exportLeaveToExcel(this.leaveList, columns, '请假记录')
        if (typeof result.count === 'number') {
          this.$message.success(`请假数据导出成功，共导出 ${result.count} 条记录`)
        } else {
          this.$message.success('请假数据导出成功，文件已生成')
        }
        this.setOperationFeedback({
          module: '请假审批',
          action: 'Excel 导出',
          status: 'success',
          result: '导出成功',
          count: typeof result.count === 'number' ? result.count : null,
          filename: result.filename,
          description: '请假数据导出请求已完成，浏览器已生成下载文件',
        })
      } catch (error) {
        const reason = error.message || '请假数据导出失败'
        this.$message.error(reason)
        this.setOperationFeedback({
          module: '请假审批',
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
    refreshPageData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.leaveListShow = this.leaveList.slice(start, end)
    },
    async getLeaveList() {
      this.loading = true
      try {
        const params = {}
        if (this.searchQuery.employee_id) params.employee_id = this.searchQuery.employee_id
        if (this.searchQuery.status) params.status = this.searchQuery.status

        const { data: res } = await this.$http.get('/api/leave/', { params })
        if (Array.isArray(res)) {
          this.leaveList = res
          this.total = res.length
          this.currentPage = 1
          this.refreshPageData()
        } else {
          this.leaveList = []
          this.leaveListShow = []
          this.total = 0
          this.$message.error('获取请假列表失败')
        }
      } catch (error) {
        console.error('获取请假列表失败:', error)
        this.$message.error(getErrorMessage(error, '获取请假列表失败'))
      } finally {
        this.loading = false
      }
    },
    resetSearch() {
      this.searchQuery = { employee_id: '', status: '' }
      this.currentPage = 1
      this.getLeaveList()
    },
    showAddDialog() {
      this.dialogTitle = '新增请假'
      this.isEdit = false
      this.currentId = null
      this.dialogVisible = true
    },
    showEditDialog(row) {
      this.dialogTitle = '编辑请假'
      this.isEdit = true
      this.currentId = row.id
      this.form = {
        employee: row.employee_id,
        type: row.type || '',
        start_time: row.start_time || '',
        end_time: row.end_time || '',
        hours: row.hours != null ? Number(row.hours) : null,
        reason: row.reason || '',
      }
      this.dialogVisible = true
    },
    dialogClosed() {
      this.$refs.formRef && this.$refs.formRef.resetFields()
      this.form = {
        employee: '',
        type: '',
        start_time: '',
        end_time: '',
        hours: null,
        reason: '',
      }
      this.currentId = null
      this.isEdit = false
    },
    submitForm() {
      this.$refs.formRef.validate(async (valid) => {
        if (!valid) return

        const payload = {
          employee: this.form.employee,
          type: this.form.type,
          start_time: this.form.start_time,
          end_time: this.form.end_time,
          hours: this.form.hours || null,
          reason: this.form.reason || null,
        }

        try {
          if (this.isEdit) {
            await this.$http.patch(`/api/leave/${this.currentId}/`, payload)
            this.$message.success('更新请假记录成功')
          } else {
            await this.$http.post('/api/leave/', payload)
            this.$message.success('新增请假记录成功')
          }
          this.dialogVisible = false
          this.getLeaveList()
        } catch (error) {
          const defaultMsg = this.isEdit ? '更新请假记录失败' : '新增请假记录失败'
          this.$message.error(getErrorMessage(error, defaultMsg))
        }
      })
    },
    async approveLeave(row) {
      if (this.approvingId !== null) {
        return
      }
      this.approvingId = row.id
      try {
        await this.$http.patch(`/api/leave/${row.id}/`, { status: 'APPROVED' })
        this.$message.success('请假审批通过，状态已更新')
        this.setOperationFeedback({
          module: '请假审批',
          action: '审批通过',
          status: 'success',
          result: '状态已更新',
          description: '请假申请已完成审批处理，列表数据已刷新',
        })
        this.getLeaveList()
      } catch (error) {
        const reason = getErrorMessage(error, '审批失败')
        this.$message.error(reason)
        this.setOperationFeedback({
          module: '请假审批',
          action: '审批通过',
          status: 'error',
          result: '审批失败',
          reason,
          description: '本次操作未完成，请根据错误提示检查数据或网络状态',
        })
      } finally {
        this.approvingId = null
      }
    },
    async rejectLeave(row) {
      if (this.approvingId !== null) {
        return
      }
      this.approvingId = row.id
      try {
        await this.$http.patch(`/api/leave/${row.id}/`, { status: 'REJECTED' })
        this.$message.success('请假审批已拒绝，状态已更新')
        this.setOperationFeedback({
          module: '请假审批',
          action: '审批拒绝',
          status: 'success',
          result: '状态已更新',
          description: '请假申请已完成审批处理，列表数据已刷新',
        })
        this.getLeaveList()
      } catch (error) {
        const reason = getErrorMessage(error, '审批失败')
        this.$message.error(reason)
        this.setOperationFeedback({
          module: '请假审批',
          action: '审批拒绝',
          status: 'error',
          result: '审批失败',
          reason,
          description: '本次操作未完成，请根据错误提示检查数据或网络状态',
        })
      } finally {
        this.approvingId = null
      }
    },
    deleteLeave(row) {
      this.$confirm('此操作将永久删除该请假记录，是否继续？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(async () => {
          try {
            await this.$http.delete(`/api/leave/${row.id}/`)
            this.$message.success('删除成功')
            this.getLeaveList()
          } catch (error) {
            this.$message.error(getErrorMessage(error, '删除失败'))
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

/deep/ .el-dialog {
  border-radius: 16px;
  overflow: hidden;
}

/deep/ .el-dialog__header {
  background: #f8fafc;
  border-bottom: 1px solid #e7edf5;
}

/deep/ .el-dialog__body {
  padding: 20px 22px 14px;
}

/deep/ .el-dialog__footer {
  border-top: 1px solid #e7edf5;
  background: #f8fafc;
}
</style>

