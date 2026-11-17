<template>
  <div class="biz-page">
    <section class="biz-page__hero">
      <div class="biz-page__hero-copy">
        <p class="biz-page__eyebrow">Personal Profile</p>
        <h1 class="biz-page__title">个人档案</h1>
        <p class="biz-page__description">
          查看个人基础信息、岗位归属和入职资料。当前后端权限只开放员工查看，不开放员工自行修改档案字段。
        </p>
        <div class="biz-page__meta">
          <span class="biz-page__badge">工号 {{ profile.user_id || currentUserId || '-' }}</span>
          <span class="biz-page__badge">部门 {{ profile.department_name || '未分配' }}</span>
        </div>
      </div>
      <div class="biz-page__hero-side">
        <div class="biz-page__stat">
          <p class="biz-page__stat-label">当前状态</p>
          <p class="biz-page__stat-value stat-compact">{{ statusLabel }}</p>
        </div>
      </div>
    </section>

    <el-card class="biz-page__panel">
      <div class="biz-page__toolbar">
        <div class="biz-page__toolbar-main">
          <h2 class="biz-page__toolbar-title">档案信息</h2>
          <p class="biz-page__toolbar-desc">信息来自后端员工档案接口，如发现异常需联系管理员或人事处理。</p>
        </div>
      </div>

      <div v-loading="loading" element-loading-text="加载中...">
        <el-descriptions v-if="profile.user_id" :column="2" border class="profile-descriptions">
          <el-descriptions-item label="工号">{{ profile.user_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="姓名">{{ profile.user_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="角色">{{ roleLabel }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ statusLabel }}</el-descriptions-item>
          <el-descriptions-item label="部门">{{ profile.department_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="岗位">{{ profile.position_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ profile.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ profile.email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="学历">{{ profile.education || '-' }}</el-descriptions-item>
          <el-descriptions-item label="入职日期">{{ profile.hire_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="合同到期">{{ profile.contract_end || '-' }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ profile.updated_at || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div v-else-if="!loading" class="biz-page__table-empty">
          <p class="biz-page__table-empty-title">未找到个人档案</p>
          <p class="biz-page__table-empty-desc">当前账号还没有绑定员工档案，请联系管理员检查员工信息。</p>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
export default {
  data() {
    return {
      loading: false,
      currentUserId: '',
      profile: {},
    }
  },
  computed: {
    roleLabel() {
      const map = {
        ADMIN: '管理员',
        HR: '人事',
        MANAGER: '经理',
        STAFF: '员工',
      }
      return map[this.profile.role] || this.profile.role || '-'
    },
    statusLabel() {
      const map = {
        ONBOARD: '在职',
        PROBATION: '试用',
        LEAVE: '离职',
        SUSPEND: '停薪留职',
      }
      return map[this.profile.status] || this.profile.status || '-'
    },
  },
  created() {
    this.currentUserId =
      window.sessionStorage.getItem('user_id') ||
      window.sessionStorage.getItem('user') ||
      window.sessionStorage.getItem('username') ||
      ''
    this.getProfile()
  },
  methods: {
    async getProfile() {
      this.loading = true
      try {
        const params = {}
        if (this.currentUserId) {
          params.employee_id = this.currentUserId
        }
        const { data } = await this.$http.get('/api/employees/', { params })
        const list = Array.isArray(data) ? data : []
        this.profile = list[0] || {}
      } catch (error) {
        console.error('获取个人档案失败:', error)
        this.$message.error('获取个人档案失败')
        this.profile = {}
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style scoped>
.stat-compact {
  font-size: 20px;
}

.profile-descriptions {
  margin-top: 8px;
}
</style>
