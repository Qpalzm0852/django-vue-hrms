<template>
  <div class="biz-page">
    <section class="biz-page__hero">
      <div class="biz-page__hero-copy">
        <p class="biz-page__eyebrow">Overtime Workflow</p>
        <h1 class="biz-page__title">加班申请</h1>
        <p class="biz-page__description">
          查看个人加班申请与审批状态，统一管理加班时间、时长和申请原因，并在需要时快速补提新申请。
        </p>
        <div class="biz-page__meta">
          <span class="biz-page__badge">总申请 {{ total }} 条</span>
          <span class="biz-page__badge">待审批 {{ pendingCount }} 条</span>
        </div>
      </div>
      <div class="biz-page__hero-side">
        <div class="biz-page__stat">
          <p class="biz-page__stat-label">累计加班时长</p>
          <p class="biz-page__stat-value">{{ totalOvertimeHours }}</p>
        </div>
      </div>
    </section>

    <el-card class="biz-page__panel">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-main">
          <h2 class="biz-page__toolbar-title">加班记录</h2>
          <p class="biz-page__toolbar-desc">按审批状态筛选个人加班申请，必要时可重新提交新的申请。</p>
        </div>
        <div class="biz-page__toolbar-actions">
          <el-button type="primary" icon="el-icon-plus" @click="showAddDialog">申请加班</el-button>
        </div>
      </div>

      <el-form :inline="true" class="biz-page__filters">
        <el-form-item label="状态">
          <el-select v-model="searchQuery.status" placeholder="请选择状态" clearable style="width: 150px">
            <el-option label="待审批" value="PENDING" />
            <el-option label="已通过" value="APPROVED" />
            <el-option label="已拒绝" value="REJECTED" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getOvertimeList">查询</el-button>
          <el-button type="default" icon="el-icon-refresh-right" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table
        :data="overtimeListShow"
        border
        stripe
        v-loading="loading"
        element-loading-text="加载中..."
      >
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="start_time" label="开始时间" width="180" align="center" />
        <el-table-column prop="end_time" label="结束时间" width="180" align="center" />
        <el-table-column prop="hours" label="时长(小时)" width="120" align="center">
          <template slot-scope="scope">
            {{ scope.row.hours || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" min-width="220" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="120" align="center">
          <template slot-scope="scope">
            <el-tag :type="statusTagType(scope.row.status)">
              {{ statusLabel(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="申请时间" width="180" align="center">
          <template slot-scope="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !overtimeListShow.length" class="biz-page__table-empty">
        <p class="biz-page__table-empty-title">当前没有加班申请</p>
        <p class="biz-page__table-empty-desc">可以切换状态筛选，或点击右上角按钮新建加班申请。</p>
      </div>

      <el-pagination
        class="biz-page__pagination"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
      />
    </el-card>

    <el-dialog title="申请加班" :visible.sync="dialogVisible" width="50%" @close="dialogClosed">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="110px">
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker
            v-model="form.start_time"
            type="datetime"
            value-format="yyyy-MM-dd HH:mm:ss"
            placeholder="请选择开始时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-date-picker
            v-model="form.end_time"
            type="datetime"
            value-format="yyyy-MM-dd HH:mm:ss"
            placeholder="请选择结束时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="时长(小时)" prop="hours">
          <el-input-number v-model="form.hours" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="加班原因" prop="reason">
          <el-input v-model="form.reason" type="textarea" :rows="3" placeholder="请输入加班原因" />
        </el-form-item>
      </el-form>

      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="submitting" @click="submitForm">提交</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
export default {
  data() {
    return {
      searchQuery: {
        status: '',
      },
      overtimeList: [],
      overtimeListShow: [],
      loading: false,
      currentPage: 1,
      pageSize: 10,
      total: 0,
      currentUserId: '',
      dialogVisible: false,
      submitting: false,
      form: {
        start_time: '',
        end_time: '',
        hours: null,
        reason: '',
      },
      formRules: {
        start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
        end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
      },
    }
  },
  computed: {
    pendingCount() {
      return this.overtimeList.filter((item) => item.status === 'PENDING').length
    },
    totalOvertimeHours() {
      const sum = this.overtimeList.reduce((total, item) => total + Number(item.hours || 0), 0)
      return sum ? sum.toFixed(1) : '0.0'
    },
  },
  created() {
    this.currentUserId = window.sessionStorage.getItem('user') || ''
    this.getOvertimeList()
  },
  methods: {
    async getOvertimeList() {
      this.loading = true
      try {
        const params = {
          employee_id: this.currentUserId,
        }
        if (this.searchQuery.status) {
          params.status = this.searchQuery.status
        }
        const { data } = await this.$http.get('/api/overtime/', { params })
        const list = Array.isArray(data) ? data : []
        list.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))

        this.overtimeList = list
        this.total = list.length
        this.currentPage = 1
        this.updateOvertimeListShow()
      } catch (error) {
        console.error('获取加班列表失败:', error)
        this.$message.error(this.getErrorMessage(error, '获取加班列表失败'))
        this.overtimeList = []
        this.overtimeListShow = []
        this.total = 0
      } finally {
        this.loading = false
      }
    },
    updateOvertimeListShow() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.overtimeListShow = this.overtimeList.slice(start, end)
    },
    resetSearch() {
      this.searchQuery.status = ''
      this.getOvertimeList()
    },
    showAddDialog() {
      this.dialogVisible = true
    },
    dialogClosed() {
      this.$refs.formRef && this.$refs.formRef.resetFields()
      this.form = {
        start_time: '',
        end_time: '',
        hours: null,
        reason: '',
      }
    },
    submitForm() {
      this.$refs.formRef.validate(async (valid) => {
        if (!valid) return
        if (this.submitting) return

        if (new Date(this.form.end_time) <= new Date(this.form.start_time)) {
          this.$message.warning('结束时间必须晚于开始时间')
          return
        }

        try {
          this.submitting = true
          await this.$http.post('/api/overtime/', {
            employee: this.currentUserId,
            start_time: this.form.start_time,
            end_time: this.form.end_time,
            hours: this.form.hours,
            reason: this.form.reason || '',
          })
          this.$message.success('加班申请提交成功')
          this.dialogVisible = false
          this.getOvertimeList()
        } catch (error) {
          console.error('提交加班申请失败:', error)
          this.$message.error(this.getErrorMessage(error, '提交加班申请失败'))
        } finally {
          this.submitting = false
        }
      })
    },
    statusLabel(status) {
      const map = {
        PENDING: '待审批',
        APPROVED: '已通过',
        REJECTED: '已拒绝',
      }
      return map[status] || status || '-'
    },
    statusTagType(status) {
      if (status === 'APPROVED') return 'success'
      if (status === 'REJECTED') return 'danger'
      return 'warning'
    },
    formatDateTime(dateTime) {
      if (!dateTime) return '-'
      const date = new Date(dateTime)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      const seconds = String(date.getSeconds()).padStart(2, '0')
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
    },
    handleSizeChange(val) {
      this.pageSize = val
      this.currentPage = 1
      this.updateOvertimeListShow()
    },
    handleCurrentChange(val) {
      this.currentPage = val
      this.updateOvertimeListShow()
    },
    getErrorMessage(error, defaultMsg) {
      const data = error && error.response && error.response.data
      if (!data) {
        return defaultMsg + '，请检查网络连接'
      }
      if (typeof data === 'string') {
        return data
      }
      if (data.detail) {
        if (Array.isArray(data.detail)) {
          return data.detail[0]
        }
        return String(data.detail)
      }
      const firstKey = Object.keys(data)[0]
      if (firstKey && Array.isArray(data[firstKey]) && data[firstKey].length) {
        return data[firstKey][0]
      }
      return defaultMsg
    },
  },
}
</script>

<style lang="less" scoped></style>
