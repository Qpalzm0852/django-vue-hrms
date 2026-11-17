<template>
  <div class="biz-page">
    <el-breadcrumb separator-class="el-icon-arrow-right">
      <el-breadcrumb-item :to="{ path: '/admin/home' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>考勤管理</el-breadcrumb-item>
      <el-breadcrumb-item>加班管理</el-breadcrumb-item>
    </el-breadcrumb>

    <section class="biz-page__hero">
      <div class="biz-page__hero-content">
        <span class="biz-page__eyebrow">Overtime Workflow</span>
        <h1>加班管理</h1>
        <p>统一处理加班申请、审批结果和工时归档，减少遗漏并提高考勤闭环效率。</p>
        <div class="biz-page__badges">
          <span class="biz-page__badge">总记录 {{ total }}</span>
          <span class="biz-page__badge">待审批 {{ pendingCount }}</span>
          <span class="biz-page__badge">总工时 {{ totalHours }}</span>
        </div>
      </div>
      <div class="biz-page__hero-stats">
        <article v-for="item in summaryCards" :key="item.label" class="biz-page__stat-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <small>{{ item.helper }}</small>
        </article>
      </div>
    </section>

    <el-card class="biz-page__panel" shadow="never">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-copy">
          <h2>加班记录</h2>
          <p>支持加班申请录入、审批操作和导出归档，便于管理员集中处理。</p>
        </div>
        <div class="biz-page__toolbar-actions">
          <el-button type="success" icon="el-icon-download" :loading="exporting" :disabled="exporting" @click="exportToExcel">导出Excel</el-button>
          <el-button type="primary" icon="el-icon-plus" @click="showAddDialog">新增加班</el-button>
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
          <el-button type="primary" icon="el-icon-search" @click="getOvertimeList">查询</el-button>
          <el-button type="info" icon="el-icon-refresh-right" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="overtimeListShow" border stripe style="width: 100%">
        <el-table-column type="index" label="序号" width="70" align="center" />
        <el-table-column prop="employee_id" label="工号" width="110" align="center" />
        <el-table-column prop="employee_name" label="姓名" width="110" align="center" />
        <el-table-column prop="start_time" label="开始时间" width="170" align="center" />
        <el-table-column prop="end_time" label="结束时间" width="170" align="center" />
        <el-table-column prop="hours" label="时长(小时)" width="110" align="center">
          <template slot-scope="scope">{{ scope.row.hours || '-' }}</template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" min-width="150" show-overflow-tooltip>
          <template slot-scope="scope">
            <span v-if="scope.row.reason">{{ scope.row.reason }}</span>
            <span v-else style="color: #909399">-</span>
          </template>
        </el-table-column>
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
                  <el-button type="success" icon="el-icon-check" size="mini" circle :loading="approvingId === scope.row.id" :disabled="approvingId !== null" @click="approveOvertime(scope.row)" />
                </el-tooltip>
                <el-tooltip content="拒绝" placement="top">
                  <el-button type="danger" icon="el-icon-close" size="mini" circle :loading="approvingId === scope.row.id" :disabled="approvingId !== null" @click="rejectOvertime(scope.row)" />
                </el-tooltip>
              </template>
              <el-tooltip content="编辑" placement="top">
                <el-button type="primary" icon="el-icon-edit" size="mini" circle @click="showEditDialog(scope.row)" />
              </el-tooltip>
              <el-tooltip content="删除" placement="top">
                <el-button type="danger" icon="el-icon-delete" size="mini" circle @click="deleteOvertime(scope.row)" />
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && overtimeListShow.length === 0" class="biz-page__table-empty">
        <i class="el-icon-time" />
        <strong>当前没有匹配的加班记录</strong>
        <span>可以调整员工工号或状态条件，或者直接录入新的加班申请。</span>
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

    <el-dialog :title="dialogTitle" :visible.sync="dialogVisible" width="50%" @close="dialogClosed">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="工号" prop="employee">
          <el-input v-model="form.employee" placeholder="请输入工号" clearable />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker
            v-model="form.start_time"
            type="datetime"
            placeholder="选择开始时间"
            style="width: 100%"
            value-format="yyyy-MM-dd HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-date-picker
            v-model="form.end_time"
            type="datetime"
            placeholder="选择结束时间"
            style="width: 100%"
            value-format="yyyy-MM-dd HH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="时长(小时)" prop="hours">
          <el-input-number v-model="form.hours" :precision="2" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="原因" prop="reason">
          <el-input type="textarea" v-model="form.reason" placeholder="请输入加班原因" :rows="3" />
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
import { exportToExcel } from '@/utils/excelExport'
import { getErrorMessage } from '@/utils/errorHandler'

export default {
  data() {
    return {
      searchQuery: {
        employee_id: '',
        status: '',
      },
      overtimeList: [],
      overtimeListShow: [],
      loading: false,
      exporting: false,
      approvingId: null,
      operationFeedback: null,
      currentPage: 1,
      pageSize: 15,
      total: 0,
      dialogVisible: false,
      dialogTitle: '新增加班',
      isEdit: false,
      currentId: null,
      form: {
        employee: '',
        start_time: '',
        end_time: '',
        hours: null,
        reason: '',
      },
      formRules: {
        employee: [{ required: true, message: '请输入工号', trigger: 'blur' }],
        start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
        end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
      },
    }
  },
  computed: {
    pendingCount() {
      return this.overtimeList.filter((item) => item.status === 'PENDING').length
    },
    totalHours() {
      const hours = this.overtimeList.reduce((sum, item) => sum + Number(item.hours || 0), 0)
      return `${hours.toFixed(1)}h`
    },
    summaryCards() {
      return [
        {
          label: '待审批',
          value: this.pendingCount,
          helper: '需优先处理',
        },
        {
          label: '已通过',
          value: this.overtimeList.filter((item) => item.status === 'APPROVED').length,
          helper: '审批完成',
        },
        {
          label: '已拒绝',
          value: this.overtimeList.filter((item) => item.status === 'REJECTED').length,
          helper: '已关闭流程',
        },
      ]
    },
  },
  created() {
    this.getOvertimeList()
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
      this.overtimeListShow = this.overtimeList.slice(start, end)
    },
    async getOvertimeList() {
      this.loading = true
      try {
        const params = {}
        if (this.searchQuery.employee_id) params.employee_id = this.searchQuery.employee_id
        if (this.searchQuery.status) params.status = this.searchQuery.status

        const { data: res } = await this.$http.get('/api/overtime/', { params })
        if (Array.isArray(res)) {
          this.overtimeList = res
          this.total = res.length
          this.currentPage = 1
          this.refreshPageData()
        } else {
          this.overtimeList = []
          this.overtimeListShow = []
          this.total = 0
          this.$message.error('获取加班列表失败')
        }
      } catch (error) {
        console.error('获取加班列表失败:', error)
        this.$message.error(getErrorMessage(error, '获取加班列表失败'))
      } finally {
        this.loading = false
      }
    },
    resetSearch() {
      this.searchQuery = { employee_id: '', status: '' }
      this.currentPage = 1
      this.getOvertimeList()
    },
    showAddDialog() {
      this.dialogTitle = '新增加班'
      this.isEdit = false
      this.currentId = null
      this.dialogVisible = true
    },
    showEditDialog(row) {
      this.dialogTitle = '编辑加班'
      this.isEdit = true
      this.currentId = row.id
      this.form = {
        employee: row.employee_id,
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
          start_time: this.form.start_time,
          end_time: this.form.end_time,
          hours: this.form.hours || null,
          reason: this.form.reason || null,
        }

        try {
          if (this.isEdit) {
            await this.$http.patch(`/api/overtime/${this.currentId}/`, payload)
            this.$message.success('更新加班记录成功')
          } else {
            await this.$http.post('/api/overtime/', payload)
            this.$message.success('新增加班记录成功')
          }
          this.dialogVisible = false
          this.getOvertimeList()
        } catch (error) {
          const defaultMsg = this.isEdit ? '更新加班记录失败' : '新增加班记录失败'
          this.$message.error(getErrorMessage(error, defaultMsg))
        }
      })
    },
    async approveOvertime(row) {
      if (this.approvingId !== null) {
        return
      }
      this.approvingId = row.id
      try {
        await this.$http.patch(`/api/overtime/${row.id}/`, { status: 'APPROVED' })
        this.$message.success('加班审批通过，状态已更新')
        this.setOperationFeedback({
          module: '加班审批',
          action: '审批通过',
          status: 'success',
          result: '状态已更新',
          description: '加班申请已完成审批处理，列表数据已刷新',
        })
        this.getOvertimeList()
      } catch (error) {
        const reason = getErrorMessage(error, '审批失败')
        this.$message.error(reason)
        this.setOperationFeedback({
          module: '加班审批',
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
    async rejectOvertime(row) {
      if (this.approvingId !== null) {
        return
      }
      this.approvingId = row.id
      try {
        await this.$http.patch(`/api/overtime/${row.id}/`, { status: 'REJECTED' })
        this.$message.success('加班审批已拒绝，状态已更新')
        this.setOperationFeedback({
          module: '加班审批',
          action: '审批拒绝',
          status: 'success',
          result: '状态已更新',
          description: '加班申请已完成审批处理，列表数据已刷新',
        })
        this.getOvertimeList()
      } catch (error) {
        const reason = getErrorMessage(error, '审批失败')
        this.$message.error(reason)
        this.setOperationFeedback({
          module: '加班审批',
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
    deleteOvertime(row) {
      this.$confirm('此操作将永久删除该加班记录，是否继续？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
        .then(async () => {
          try {
            await this.$http.delete(`/api/overtime/${row.id}/`)
            this.$message.success('删除成功')
            this.getOvertimeList()
          } catch (error) {
            this.$message.error(getErrorMessage(error, '删除失败'))
          }
        })
        .catch(() => {
          this.$message.info('已取消删除')
        })
    },
    async exportToExcel() {
      if (!this.overtimeList || this.overtimeList.length === 0) {
        this.$message.warning('没有数据可导出')
        return
      }
      const columns = [
        { key: 'employee_id', label: '工号' },
        { key: 'employee_name', label: '姓名' },
        { key: 'start_time', label: '开始时间' },
        { key: 'end_time', label: '结束时间' },
        { key: 'hours', label: '时长(小时)' },
        { key: 'reason', label: '原因' },
        { key: 'status', label: '状态' },
        { key: 'approver_name', label: '审批人' },
      ]
      this.exporting = true
      this.$message.info('正在生成加班数据导出文件，请稍候...')
      try {
        const result = await exportToExcel(this.overtimeList, columns, '加班记录')
        if (typeof result.count === 'number') {
          this.$message.success(`加班数据导出成功，共导出 ${result.count} 条记录`)
        } else {
          this.$message.success('加班数据导出成功，文件已生成')
        }
        this.setOperationFeedback({
          module: '加班审批',
          action: 'Excel 导出',
          status: 'success',
          result: '导出成功',
          count: typeof result.count === 'number' ? result.count : null,
          filename: result.filename,
          description: '加班数据导出请求已完成，浏览器已生成下载文件',
        })
      } catch (error) {
        const reason = error.message || '加班数据导出失败'
        this.$message.error(reason)
        this.setOperationFeedback({
          module: '加班审批',
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

/deep/ .el-breadcrumb {
  margin: 4px 0 10px;
}

/deep/ .el-breadcrumb__inner {
  color: #355d92;
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

@media (max-width: 768px) {
  .action-buttons {
    gap: 6px;
  }
}
</style>

