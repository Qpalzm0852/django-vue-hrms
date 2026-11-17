<template>
  <div class="biz-page">
    <section class="biz-page__hero">
      <div class="biz-page__hero-copy">
        <p class="biz-page__eyebrow">Payroll Center</p>
        <h1 class="biz-page__title">我的工资条</h1>
        <p class="biz-page__description">
          按月份查看工资构成、扣减项和实发金额。筛选后可快速核对当月薪酬是否已经确认发放。
        </p>
        <div class="biz-page__meta">
          <span class="biz-page__badge">工资记录 {{ total }} 条</span>
          <span class="biz-page__badge">当前页 {{ payrollListShow.length }} 条</span>
        </div>
      </div>
      <div class="biz-page__hero-side">
        <div class="biz-page__stat">
          <p class="biz-page__stat-label">最近实发工资</p>
          <p class="biz-page__stat-value">¥{{ latestNetPay }}</p>
        </div>
      </div>
    </section>

    <el-card class="biz-page__panel">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-main">
          <h2 class="biz-page__toolbar-title">工资明细列表</h2>
          <p class="biz-page__toolbar-desc">支持按月份筛选，点击“查看”可展开查看完整工资条。</p>
        </div>
      </div>

      <el-form :inline="true" class="biz-page__filters">
        <el-form-item label="月份">
          <el-date-picker
            v-model="searchQuery.period"
            type="month"
            placeholder="选择月份"
            value-format="yyyy-MM"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="getPayrollList">查询</el-button>
          <el-button type="default" icon="el-icon-refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table
        v-loading="loading"
        :data="payrollListShow"
        border
        stripe
        style="width: 100%"
        element-loading-text="加载中..."
      >
        <el-table-column type="index" label="序号" width="70" align="center" />
        <el-table-column prop="period" label="月份" width="120" align="center" />
        <el-table-column prop="base_pay" label="基本工资" width="120" align="right">
          <template slot-scope="scope"><span class="money-text">¥{{ formatMoney(scope.row.base_pay) }}</span></template>
        </el-table-column>
        <el-table-column prop="allowance" label="津贴" width="120" align="right">
          <template slot-scope="scope"><span class="money-text">¥{{ formatMoney(scope.row.allowance) }}</span></template>
        </el-table-column>
        <el-table-column prop="bonus" label="奖金" width="120" align="right">
          <template slot-scope="scope"><span class="money-text">¥{{ formatMoney(scope.row.bonus) }}</span></template>
        </el-table-column>
        <el-table-column prop="deduction" label="扣除" width="120" align="right">
          <template slot-scope="scope"><span class="money-text deduction-text">-¥{{ formatMoney(scope.row.deduction) }}</span></template>
        </el-table-column>
        <el-table-column prop="tax" label="个税" width="120" align="right">
          <template slot-scope="scope"><span class="money-text deduction-text">-¥{{ formatMoney(scope.row.tax) }}</span></template>
        </el-table-column>
        <el-table-column prop="social_security" label="社保" width="120" align="right">
          <template slot-scope="scope"><span class="money-text deduction-text">-¥{{ formatMoney(scope.row.social_security) }}</span></template>
        </el-table-column>
        <el-table-column prop="housing_fund" label="公积金" width="120" align="right">
          <template slot-scope="scope"><span class="money-text deduction-text">-¥{{ formatMoney(scope.row.housing_fund) }}</span></template>
        </el-table-column>
        <el-table-column prop="net_pay" label="实发工资" width="140" align="right">
          <template slot-scope="scope"><span class="money-text net-pay-text">¥{{ formatMoney(scope.row.net_pay) }}</span></template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template slot-scope="scope">
            <el-tag :type="scope.row.status === 'CONFIRMED' ? 'success' : 'info'">
              {{ scope.row.status === 'CONFIRMED' ? '已确认' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" align="center" fixed="right">
          <template slot-scope="scope">
            <el-button type="primary" size="mini" icon="el-icon-view" @click="viewDetail(scope.row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !payrollListShow.length" class="biz-page__table-empty">
        <p class="biz-page__table-empty-title">当前没有工资记录</p>
        <p class="biz-page__table-empty-desc">可以尝试切换月份筛选，或等待薪酬核算完成后再查看。</p>
      </div>

      <el-pagination
        class="biz-page__pagination"
        :current-page="currentPage"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>

    <el-dialog title="工资条详情" :visible.sync="detailDialogVisible" width="640px">
      <div class="payroll-detail" v-if="currentPayroll">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="月份">{{ currentPayroll.period }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentPayroll.status === 'CONFIRMED' ? 'success' : 'info'">
              {{ currentPayroll.status === 'CONFIRMED' ? '已确认' : '草稿' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="基本工资" :span="2"><span class="money-text">¥{{ formatMoney(currentPayroll.base_pay) }}</span></el-descriptions-item>
          <el-descriptions-item label="津贴"><span class="money-text">¥{{ formatMoney(currentPayroll.allowance) }}</span></el-descriptions-item>
          <el-descriptions-item label="奖金"><span class="money-text">¥{{ formatMoney(currentPayroll.bonus) }}</span></el-descriptions-item>
          <el-descriptions-item label="扣除" :span="2"><span class="money-text deduction-text">-¥{{ formatMoney(currentPayroll.deduction) }}</span></el-descriptions-item>
          <el-descriptions-item label="个税"><span class="money-text deduction-text">-¥{{ formatMoney(currentPayroll.tax) }}</span></el-descriptions-item>
          <el-descriptions-item label="社保"><span class="money-text deduction-text">-¥{{ formatMoney(currentPayroll.social_security) }}</span></el-descriptions-item>
          <el-descriptions-item label="公积金"><span class="money-text deduction-text">-¥{{ formatMoney(currentPayroll.housing_fund) }}</span></el-descriptions-item>
          <el-descriptions-item label="实发工资" :span="2">
            <span class="money-text net-pay-text detail-net-pay">¥{{ formatMoney(currentPayroll.net_pay) }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
export default {
  data() {
    return {
      searchQuery: {
        period: '',
      },
      payrollList: [],
      payrollListShow: [],
      loading: false,
      currentPage: 1,
      pageSize: 10,
      total: 0,
      detailDialogVisible: false,
      currentPayroll: null,
      currentUserId: '',
    }
  },
  computed: {
    latestNetPay() {
      if (!this.payrollList.length) return '0.00'
      return this.formatMoney(this.payrollList[0].net_pay)
    },
  },
  created() {
    this.currentUserId =
      window.sessionStorage.getItem('user_id') ||
      window.sessionStorage.getItem('user') ||
      window.sessionStorage.getItem('username') ||
      ''
    this.getPayrollList()
  },
  methods: {
    formatMoney(value) {
      if (value === null || value === undefined || value === '') return '0.00'
      return Number(value).toFixed(2)
    },
    refreshPageData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.payrollListShow = this.payrollList.slice(start, end)
    },
    async getPayrollList() {
      this.loading = true
      try {
        const params = {}
        if (this.currentUserId) {
          params.employee_id = this.currentUserId
        }
        if (this.searchQuery.period) {
          params.period = this.searchQuery.period
        }

        const { data: res } = await this.$http.get('/api/payroll/', { params })
        if (Array.isArray(res)) {
          this.payrollList = res.sort((a, b) => (b.period || '').localeCompare(a.period || ''))
          this.total = this.payrollList.length
          this.currentPage = 1
          this.refreshPageData()
        } else {
          this.payrollList = []
          this.payrollListShow = []
          this.total = 0
        }
      } catch (error) {
        console.error('获取工资条列表失败:', error)
        const errorMsg = this.getErrorMessage(error, '获取工资条列表失败')
        this.$message.error(errorMsg)
        this.payrollList = []
        this.payrollListShow = []
        this.total = 0
      } finally {
        this.loading = false
      }
    },
    resetSearch() {
      this.searchQuery = { period: '' }
      this.getPayrollList()
    },
    viewDetail(row) {
      this.currentPayroll = row
      this.detailDialogVisible = true
    },
    handleSizeChange(val) {
      this.pageSize = val
      this.currentPage = 1
      this.refreshPageData()
    },
    handleCurrentChange(val) {
      this.currentPage = val
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

      if (typeof data === 'string') {
        return data
      }

      return defaultMsg
    },
  },
}
</script>

<style lang="less" scoped>
.money-text {
  color: #204f48;
  font-weight: 600;
}

.deduction-text {
  color: #e53935;
}

.net-pay-text {
  color: #16a34a;
  font-weight: 700;
}

.detail-net-pay {
  font-size: 20px;
  font-weight: 700;
}

.payroll-detail {
  padding: 6px 0;
}
</style>
