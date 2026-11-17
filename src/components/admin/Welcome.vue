<template>
  <div class="welcome-page admin-welcome">
    <section class="welcome-hero">
      <div class="welcome-hero__copy">
        <p class="welcome-hero__eyebrow">Admin Console</p>
        <h2>欢迎回来，{{ userDisplayName }}</h2>
        <p class="welcome-hero__description">
          今天共有 {{ overviewData ? overviewData.pending_total || 0 : 0 }} 条待审批事项，组织效率保持稳定。把审批、薪酬和招聘决策集中在一个首页处理。
        </p>
        <p class="welcome-hero__time">{{ currentTime }}</p>
        <div class="welcome-hero__actions">
          <button class="welcome-btn welcome-btn--primary" @click="$router.push('/admin/selections')">查看审批</button>
          <button class="welcome-btn welcome-btn--ghost" @click="$router.push('/admin/dashboard')">查看报告</button>
        </div>
      </div>

      <aside class="welcome-hero__aside">
        <div class="hero-panel">
          <span class="hero-panel__label">今日摘要</span>
          <strong>{{ overviewData ? overviewData.pending_total || 0 : 0 }}</strong>
          <p>需要管理员优先跟进的待处理事项</p>
        </div>
        <div class="hero-list">
          <div class="hero-list__item">
            <span>新增员工</span>
            <strong>{{ overviewData ? overviewData.new_employees || 0 : 0 }}</strong>
          </div>
          <div class="hero-list__item">
            <span>今日出勤</span>
            <strong>{{ overviewData ? overviewData.today_attendance || 0 : 0 }}</strong>
          </div>
          <div class="hero-list__item">
            <span>部门覆盖</span>
            <strong>{{ overviewData ? overviewData.total_departments || 0 : 0 }}</strong>
          </div>
        </div>
      </aside>
      <div class="welcome-hero__glow" />
    </section>

    <section class="welcome-stats">
      <button v-for="(stat, index) in stats" :key="index" class="stat-card" type="button" @click="handleStatClick(stat.path)">
        <span class="stat-card__label">{{ stat.label }}</span>
        <div class="stat-card__value-row">
          <strong>{{ stat.value }}</strong>
          <span v-if="stat.trendText" class="stat-card__meta stat-card__meta--accent">{{ stat.trendText }}</span>
          <span v-else class="stat-card__meta">{{ index === 2 ? (stat.value > 0 ? '需处理' : '已清空') : index === 3 ? '组织规模' : '今日概览' }}</span>
        </div>
      </button>
    </section>

    <section class="welcome-layout">
      <article class="workspace-card workspace-card--feature" @click="handleModuleClick('/admin/departments')">
        <div>
          <p class="workspace-card__eyebrow">组织与人员</p>
          <h3>从架构到员工档案，一处完成治理</h3>
          <p>部门、岗位、员工通讯录和生命周期事件已经收口到同一条管理链路。</p>
        </div>
        <div class="workspace-card__footer">
          <span>进入组织架构</span>
          <span class="material-symbols-outlined">arrow_forward</span>
        </div>
      </article>

      <aside class="quick-panel">
        <p class="quick-panel__title">快捷操作</p>
        <button v-for="(action, index) in quickActions" :key="index" class="quick-panel__action" type="button" @click="handleQuickAction(action.path)">
          <span class="quick-panel__icon material-symbols-outlined">{{ action.materialIcon }}</span>
          <span>{{ action.label }}</span>
        </button>
      </aside>

      <button
        v-for="module in modules.slice(1)"
        :key="module.title"
        type="button"
        class="workspace-card"
        @click="handleModuleClick(module.path)"
      >
        <div>
          <p class="workspace-card__eyebrow">{{ module.title }}</p>
          <h3>{{ module.description }}</h3>
        </div>
        <div class="workspace-card__footer">
          <span>打开模块</span>
          <span class="material-symbols-outlined">north_east</span>
        </div>
      </button>

      <article class="workspace-banner">
        <div>
          <p class="workspace-card__eyebrow">招聘加速</p>
          <h3>智能招聘系统已经接入首页工作流</h3>
          <p>从需求发布、简历管理到面试安排，招聘链路已经适合直接作为管理入口使用。</p>
        </div>
        <button class="welcome-btn welcome-btn--dark" @click="handleModuleClick('/admin/recruitment')">进入招聘门户</button>
      </article>
    </section>
  </div>
</template>

<script>
export default {
  name: 'Welcome',
  data() {
    return {
      currentTime: '',
      overviewData: null,
      loading: false,
      clockTimer: null,
      statsTimer: null,
      stats: [
        {
          icon: 'el-icon-user-solid',
          value: 0,
          label: '员工总数',
          gradient: 'linear-gradient(135deg, #4f6d8f 0%, #446181 100%)',
          path: '/admin/students',
          trend: false,
          trendIcon: '',
          trendText: '',
        },
        {
          icon: 'el-icon-date',
          value: 0,
          label: '今日考勤',
          gradient: 'linear-gradient(135deg, #7d657f 0%, #705a72 100%)',
          path: '/admin/scores',
          trend: false,
          trendIcon: '',
          trendText: '',
        },
        {
          icon: 'el-icon-warning-outline',
          value: 0,
          label: '待审批事项',
          gradient: 'linear-gradient(135deg, #4e7f8f 0%, #426f7f 100%)',
          path: '/admin/selections',
          trend: false,
          trendIcon: '',
          trendText: '',
        },
        {
          icon: 'el-icon-s-home',
          value: 0,
          label: '部门总数',
          gradient: 'linear-gradient(135deg, #5f7f6b 0%, #526f5e 100%)',
          path: null,
          trend: false,
          trendIcon: '',
          trendText: '',
        },
      ],
      modules: [
        {
          icon: 'el-icon-s-home',
          title: '组织管理',
          description: '部门与岗位配置，组织架构维护',
          color: 'linear-gradient(135deg, #4f6d8f 0%, #446181 100%)',
          path: '/admin/students',
        },
        {
          icon: 'el-icon-user-solid',
          title: '员工管理',
          description: '员工档案、绩效、培训与公告管理',
          color: 'linear-gradient(135deg, #7d657f 0%, #705a72 100%)',
          path: '/admin/students',
        },
        {
          icon: 'el-icon-time',
          title: '考勤管理',
          description: '考勤记录、请假审批与加班审批',
          color: 'linear-gradient(135deg, #4e7f8f 0%, #426f7f 100%)',
          path: '/admin/scores',
        },
        {
          icon: 'el-icon-coin',
          title: '薪酬管理',
          description: '薪酬核算与工资发放管理',
          color: 'linear-gradient(135deg, #5f7f6b 0%, #526f5e 100%)',
          path: '/admin/scoresAnalysis',
        },
        {
          icon: 'el-icon-s-data',
          title: '数据统计',
          description: '多维数据统计与分析报表',
          color: 'linear-gradient(135deg, #7f7052 0%, #706248 100%)',
          path: '/admin/dashboard',
        },
        {
          icon: 'el-icon-s-custom',
          title: '招聘管理',
          description: '招聘需求、简历管理与面试安排',
          color: 'linear-gradient(135deg, #5c7082 0%, #506376 100%)',
          path: '/admin/recruitment',
        },
      ],
      quickActions: [
        { icon: 'el-icon-user', materialIcon: 'person_add', label: '添加员工', path: '/admin/students' },
        { icon: 'el-icon-document', materialIcon: 'history_edu', label: '补录考勤', path: '/admin/scores' },
        { icon: 'el-icon-tickets', materialIcon: 'request_quote', label: '运行薪资结算', path: '/admin/scoresAnalysis' },
        { icon: 'el-icon-alarm-clock', materialIcon: 'post_add', label: '发布职位', path: '/admin/recruitment' },
      ],
    }
  },
  computed: {
    userDisplayName() {
      return window.sessionStorage.getItem('user_name') || 'Admin'
    },
  },
  mounted() {
    this.updateTime()
    this.loadOverviewData()

    this.clockTimer = setInterval(() => {
      this.updateTime()
    }, 1000)

    this.statsTimer = setInterval(() => {
      this.loadOverviewData()
    }, 300000)
  },
  beforeDestroy() {
    if (this.clockTimer) {
      clearInterval(this.clockTimer)
    }
    if (this.statsTimer) {
      clearInterval(this.statsTimer)
    }
  },
  methods: {
    updateTime() {
      const now = new Date()
      const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        weekday: 'long',
      }
      this.currentTime = now.toLocaleString('zh-CN', options)
    },
    async loadOverviewData() {
      this.loading = true
      try {
        const { data } = await this.$http.get('/api/statistics/overview/')
        this.overviewData = data || {}

        this.stats[0].value = data.total_employees || 0
        this.stats[1].value = data.today_attendance || 0
        this.stats[2].value = data.pending_total || 0
        this.stats[3].value = data.total_departments || 0

        this.stats[2].trend = data.pending_total > 0
        this.stats[2].trendIcon = data.pending_total > 0 ? 'el-icon-warning' : ''
        this.stats[2].trendText = data.pending_total > 0 ? '需要处理' : ''

        this.stats[0].trend = data.new_employees > 0
        this.stats[0].trendIcon = data.new_employees > 0 ? 'el-icon-top' : ''
        this.stats[0].trendText = data.new_employees > 0 ? `+${data.new_employees}` : ''
      } catch (error) {
        console.error('获取首页统计数据失败:', error)
        this.stats.forEach((stat) => {
          if (typeof stat.value === 'number') {
            stat.value = 0
          }
          stat.trend = false
          stat.trendIcon = ''
          stat.trendText = ''
        })
      } finally {
        this.loading = false
      }
    },
    handleStatClick(path) {
      if (path) {
        this.$router.push(path)
      }
    },
    handleModuleClick(path) {
      if (path) {
        this.$router.push(path)
      }
    },
    handleQuickAction(path) {
      this.$router.push(path)
    },
  },
}
</script>

<style scoped>
.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

.welcome-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding-bottom: 8px;
}

.welcome-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(260px, 0.8fr);
  gap: 18px;
  padding: 28px;
  border-radius: 18px;
  overflow: hidden;
  background:
    radial-gradient(circle at top right, rgba(196, 200, 184, 0.28), transparent 24%),
    linear-gradient(145deg, #edece6 0%, #e4e5dd 100%);
  border: 1px solid #d3d5cb;
  box-shadow: 0 14px 28px rgba(34, 35, 30, 0.05);
}

.welcome-hero__copy,
.welcome-hero__aside {
  position: relative;
  z-index: 1;
}

.welcome-hero__eyebrow,
.workspace-card__eyebrow {
  margin: 0 0 10px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.welcome-hero__eyebrow {
  color: #707264;
}

.welcome-hero h2 {
  margin: 0;
  color: #232722;
  font-size: clamp(30px, 4vw, 44px);
  line-height: 1.1;
  letter-spacing: -0.04em;
  font-weight: 700;
}

.welcome-hero__description {
  max-width: 620px;
  margin: 14px 0 0;
  color: #5f635d;
  font-size: 14px;
  line-height: 1.85;
}

.welcome-hero__time {
  margin: 16px 0 0;
  color: #83837c;
  font-size: 12px;
}

.welcome-hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 24px;
}

.welcome-btn {
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.18s ease, background-color 0.18s ease, color 0.18s ease, border-color 0.18s ease;
}

.welcome-btn:hover {
  transform: translateY(-1px);
}

.welcome-btn--primary {
  background: #2c312b;
  color: #f3f2ec;
}

.welcome-btn--ghost {
  color: #373b34;
  background: rgba(255, 255, 255, 0.56);
  border: 1px solid #d8d8cf;
}

.welcome-btn--dark {
  background: #2b302b;
  color: #f2f0eb;
}

.welcome-hero__aside {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hero-panel,
.hero-list {
  border-radius: 16px;
  border: 1px solid #d6d8cf;
  background: rgba(250, 249, 245, 0.8);
}

.hero-panel {
  padding: 20px;
}

.hero-panel__label {
  display: block;
  color: #7a7b70;
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.hero-panel strong {
  display: block;
  margin-top: 12px;
  color: #232823;
  font-size: 36px;
  line-height: 1;
  letter-spacing: -0.05em;
}

.hero-panel p {
  margin: 12px 0 0;
  color: #6b6e67;
  font-size: 13px;
  line-height: 1.7;
}

.hero-list {
  padding: 10px 18px;
}

.hero-list__item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 13px 0;
  border-bottom: 1px solid #e6e6de;
  color: #70736d;
  font-size: 13px;
}

.hero-list__item:last-child {
  border-bottom: none;
}

.hero-list__item strong {
  color: #2b302b;
  font-size: 17px;
}

.welcome-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.stat-card {
  text-align: left;
  cursor: pointer;
  border: 1px solid #d9dbd2;
  border-radius: 16px;
  background: linear-gradient(180deg, #f8f7f3 0%, #f0efea 100%);
  padding: 18px;
  box-shadow: 0 4px 10px rgba(38, 39, 34, 0.03);
}

.stat-card__label {
  display: block;
  color: #77786f;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.stat-card__value-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 10px;
  margin-top: 18px;
}

.stat-card__value-row strong {
  color: #232722;
  font-size: 34px;
  line-height: 1;
  letter-spacing: -0.05em;
}

.stat-card__meta {
  color: #85867f;
  font-size: 12px;
  font-weight: 700;
}

.stat-card__meta--accent {
  color: #5e6957;
}

.welcome-layout {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.workspace-card,
.quick-panel,
.workspace-banner {
  border-radius: 16px;
  border: 1px solid #d9dcd4;
  background: #f6f5f1;
  box-shadow: 0 8px 18px rgba(34, 35, 30, 0.04);
}

.workspace-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 208px;
  padding: 22px;
  text-align: left;
  cursor: pointer;
}

.workspace-card--feature {
  grid-column: span 2;
  min-height: 240px;
  background: linear-gradient(180deg, #efeee8 0%, #e8e8df 100%);
}

.workspace-card__eyebrow {
  color: #808076;
}

.workspace-card h3,
.workspace-banner h3 {
  margin: 0;
  color: #242823;
  font-size: 24px;
  line-height: 1.24;
  letter-spacing: -0.03em;
}

.workspace-card p,
.workspace-banner p {
  margin: 12px 0 0;
  color: #666962;
  font-size: 14px;
  line-height: 1.75;
}

.workspace-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 22px;
  color: #4f5a49;
  font-size: 13px;
  font-weight: 700;
}

.quick-panel {
  padding: 20px;
}

.quick-panel__title {
  margin: 0 0 14px;
  color: #242823;
  font-size: 14px;
  font-weight: 800;
}

.quick-panel__action {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 0;
  border: none;
  border-bottom: 1px solid #e8e7e0;
  background: transparent;
  color: #4b534d;
  font-size: 14px;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
}

.quick-panel__action:last-child {
  border-bottom: none;
}

.quick-panel__icon {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #ecece6;
  color: #565d55;
  font-size: 18px;
}

.workspace-banner {
  grid-column: span 3;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  padding: 24px;
  background: linear-gradient(180deg, #eceee6 0%, #f4f4ee 100%);
}

@media (max-width: 1100px) {
  .welcome-hero,
  .welcome-layout {
    grid-template-columns: 1fr;
  }

  .workspace-card--feature,
  .workspace-banner {
    grid-column: span 1;
  }

  .welcome-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 680px) {
  .welcome-hero,
  .workspace-card,
  .quick-panel,
  .workspace-banner {
    padding: 20px;
  }

  .welcome-stats {
    grid-template-columns: 1fr;
  }

  .workspace-banner {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
