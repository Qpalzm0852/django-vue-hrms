<template>
  <div class="welcome-page employee-welcome">
    <section class="welcome-hero">
      <div class="welcome-hero__copy">
        <p class="welcome-hero__eyebrow">Personal Desk</p>
        <h2>欢迎回来，{{ userDisplayName }}</h2>
        <p class="welcome-hero__description">
          你的工资、考勤、请假和加班进度已经汇总到这里。首页的目标不是展示功能，而是让你 10 秒内知道今天该处理什么。
        </p>
        <p class="welcome-hero__time">{{ currentTime }}</p>
        <div class="welcome-hero__actions">
          <button class="welcome-btn welcome-btn--primary" @click="$router.push('/employee/attendance')">查看本月考勤</button>
          <button class="welcome-btn welcome-btn--ghost" @click="$router.push('/employee/payroll')">查看工资条</button>
        </div>
      </div>

      <aside class="welcome-hero__aside">
        <div class="hero-panel">
          <span class="hero-panel__label">待办总数</span>
          <strong>{{ pendingTotal }}</strong>
          <p>需要你跟进的请假、加班或异常记录</p>
        </div>
        <div class="hero-list">
          <div class="hero-list__item">
            <span>本月出勤</span>
            <strong>{{ stats[0].value }}</strong>
          </div>
          <div class="hero-list__item">
            <span>请假次数</span>
            <strong>{{ stats[1].value }}</strong>
          </div>
          <div class="hero-list__item">
            <span>异常记录</span>
            <strong>{{ stats[3].value }}</strong>
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
          <span class="stat-card__meta" :class="{ 'stat-card__meta--danger': stat.label === '异常记录' && stat.value > 0 }">{{ stat.meta }}</span>
        </div>
      </button>
    </section>

    <section class="welcome-layout">
      <article class="workspace-card workspace-card--feature">
        <div class="workspace-card__head">
          <div>
            <p class="workspace-card__eyebrow">待办中心</p>
            <h3>本周需要你处理的事项</h3>
          </div>
          <span class="workspace-chip">{{ pendingTotal }} 项</span>
        </div>

        <div v-if="todoItems.length" class="todo-list">
          <button v-for="item in todoItems" :key="item.title" class="todo-item" type="button" @click="handleQuickAction(item.path)">
            <span class="todo-item__icon material-symbols-outlined">{{ item.icon }}</span>
            <span class="todo-item__body">
              <strong>{{ item.title }}</strong>
              <small>{{ item.description }}</small>
            </span>
          </button>
        </div>

        <div v-else class="empty-note">
          <strong>当前没有待办事项</strong>
          <p>本周的请假、加班和异常记录都已处理完毕，可以继续查看培训和绩效进展。</p>
        </div>
      </article>

      <aside class="quick-panel">
        <p class="quick-panel__title">常用服务</p>
        <button v-for="action in quickActions" :key="action.label" class="quick-panel__action" type="button" @click="handleQuickAction(action.path)">
          <span class="quick-panel__icon material-symbols-outlined">{{ action.materialIcon }}</span>
          <span>{{ action.label }}</span>
        </button>
      </aside>

      <button
        v-for="module in modules"
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
          <span>进入模块</span>
          <span class="material-symbols-outlined">north_east</span>
        </div>
      </button>
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
        { value: 0, label: '本月出勤', path: '/employee/attendance', accentClass: 'bg-secondary', meta: '', metaClass: 'text-secondary' },
        { value: 0, label: '请假次数', path: '/employee/leave', accentClass: 'bg-primary', meta: '', metaClass: 'text-slate-400' },
        { value: 0, label: '加班次数', path: '/employee/overtime', accentClass: 'bg-secondary opacity-40', meta: '', metaClass: 'text-slate-400' },
        { value: 0, label: '异常记录', path: '/employee/attendance', accentClass: 'bg-error', meta: '状态正常', metaClass: 'text-slate-400' },
      ],
      modules: [
        {
          title: '我的工资条',
          description: '查看薪资构成、实发金额和历史发放记录。',
          path: '/employee/payroll',
          icon: 'receipt_long',
          tintClass: 'bg-primary/10',
          iconClass: 'text-primary',
        },
        {
          title: '我的考勤',
          description: '查看月度出勤、打卡记录和异常明细。',
          path: '/employee/attendance',
          icon: 'event_available',
          tintClass: 'bg-secondary/10',
          iconClass: 'text-secondary',
        },
        {
          title: '请假与加班',
          description: '提交申请并追踪审批进度，不再反复切换页面。',
          path: '/employee/leave',
          icon: 'pending_actions',
          tintClass: 'bg-primary/10',
          iconClass: 'text-primary',
        },
      ],
      quickActions: [
        { materialIcon: 'receipt', label: '查看工资条', path: '/employee/payroll' },
        { materialIcon: 'today', label: '打开考勤记录', path: '/employee/attendance' },
        { materialIcon: 'event_busy', label: '发起请假申请', path: '/employee/leave' },
        { materialIcon: 'schedule_send', label: '提交加班申请', path: '/employee/overtime' },
      ],
    }
  },
  computed: {
    userDisplayName() {
      return window.sessionStorage.getItem('user_name') || '员工'
    },
    pendingTotal() {
      if (!this.overviewData) return 0
      return Number(this.overviewData.pending_total || 0)
    },
    todoItems() {
      if (!this.overviewData) return []
      const items = []

      if (Number(this.overviewData.pending_leave || 0) > 0) {
        items.push({
          title: '请假申请待处理',
          description: `当前有 ${this.overviewData.pending_leave} 条请假记录等待跟进。`,
          icon: 'event_busy',
          path: '/employee/leave',
        })
      }

      if (Number(this.overviewData.pending_overtime || 0) > 0) {
        items.push({
          title: '加班申请待处理',
          description: `当前有 ${this.overviewData.pending_overtime} 条加班记录等待确认。`,
          icon: 'schedule',
          path: '/employee/overtime',
        })
      }

      if (Number(this.overviewData.month_abnormal_count || 0) > 0) {
        items.push({
          title: '考勤异常需要关注',
          description: `本月共有 ${this.overviewData.month_abnormal_count} 条异常记录，请及时核对。`,
          icon: 'warning',
          path: '/employee/attendance',
        })
      }

      return items
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
        const { data } = await this.$http.get('/api/statistics/employee-overview/')
        this.overviewData = data || {}

        this.stats[0].value = data.month_work_days || 0
        this.stats[0].meta = data.month_work_days > 0 ? '出勤稳定' : '暂无记录'

        this.stats[1].value = data.month_leave_count || 0
        this.stats[1].meta = data.month_leave_count > 0 ? '已提交' : '本月无请假'

        this.stats[2].value = data.month_overtime_count || 0
        this.stats[2].meta = data.month_overtime_count > 0 ? '已记录' : '本月无加班'

        this.stats[3].value = data.month_abnormal_count || 0
        this.stats[3].meta = data.month_abnormal_count > 0 ? '需要关注' : '状态正常'
        this.stats[3].metaClass = data.month_abnormal_count > 0 ? 'text-error' : 'text-slate-400'
      } catch (error) {
        console.error('获取首页统计数据失败:', error)
        this.stats.forEach((stat) => {
          stat.value = 0
          stat.meta = '暂无记录'
        })
        this.stats[3].meta = '状态正常'
        this.stats[3].metaClass = 'text-slate-400'
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

.welcome-hero__copy {
  padding-right: 18px;
  border-right: 1px solid rgba(72, 68, 58, 0.14);
}

.welcome-hero__eyebrow,
.workspace-card__eyebrow {
  margin: 0 0 10px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.24em;
  text-transform: uppercase;
}

.welcome-hero__eyebrow {
  color: #7a6e5f;
}

.welcome-hero h2 {
  margin: 0;
  color: #26231d;
  font-family: 'Georgia', 'Times New Roman', serif;
  font-size: clamp(36px, 4.8vw, 54px);
  line-height: 0.98;
  letter-spacing: -0.05em;
  font-weight: 700;
  max-width: 10ch;
}

.welcome-hero__description {
  max-width: 620px;
  margin: 18px 0 0;
  color: #5e574d;
  font-size: 15px;
  line-height: 1.9;
}

.welcome-hero__time {
  margin: 20px 0 0;
  color: #887f73;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.welcome-hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 26px;
}

.welcome-btn {
  border-radius: 999px;
  padding: 12px 18px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  cursor: pointer;
  transition: transform 0.18s ease, background-color 0.18s ease, color 0.18s ease, border-color 0.18s ease;
}

.welcome-btn:hover {
  transform: translateY(-1px);
}

.welcome-btn--primary {
  border: 1px solid #2f342d;
  background: #2f342d;
  color: #f3f2ec;
}

.welcome-btn--ghost {
  color: #373b34;
  background: rgba(255, 255, 255, 0.56);
  border: 1px solid #d8d8cf;
}

.welcome-hero__aside {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hero-panel,
.hero-list {
  border-radius: 8px;
  border: 1px solid #d3cec4;
  background: rgba(247, 244, 237, 0.72);
}

.hero-panel {
  padding: 18px;
}

.hero-panel__label {
  display: block;
  color: #877d70;
  font-size: 10px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}

.hero-panel strong {
  display: block;
  margin-top: 12px;
  color: #26231d;
  font-family: 'Georgia', 'Times New Roman', serif;
  font-size: 42px;
  line-height: 1;
  letter-spacing: -0.05em;
}

.hero-panel p {
  margin: 12px 0 0;
  color: #6d665c;
  font-size: 12px;
  line-height: 1.8;
}

.hero-list {
  padding: 10px 18px;
}

.hero-list__item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px solid #e6e6de;
  color: #72695f;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.hero-list__item:last-child {
  border-bottom: none;
}

.hero-list__item strong {
  color: #2d3029;
  font-size: 16px;
  letter-spacing: normal;
}

.welcome-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.stat-card {
  text-align: left;
  cursor: pointer;
  border: 1px solid #d8d4ca;
  border-radius: 8px;
  background: linear-gradient(180deg, #f6f3ed 0%, #efede6 100%);
  padding: 18px 16px;
  box-shadow: none;
}

.stat-card__label {
  display: block;
  color: #877d70;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.2em;
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
  color: #26231d;
  font-family: 'Georgia', 'Times New Roman', serif;
  font-size: 36px;
  line-height: 1;
  letter-spacing: -0.05em;
}

.stat-card__meta {
  color: #847d72;
  font-size: 11px;
  font-weight: 700;
}

.stat-card__meta--danger {
  color: #9f5d5d;
}

.welcome-layout {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.workspace-card,
.quick-panel {
  border-radius: 8px;
  border: 1px solid #d7d2c7;
  background: #f4f1eb;
  box-shadow: 0 10px 20px rgba(34, 35, 30, 0.035);
}

.workspace-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 214px;
  padding: 24px;
  text-align: left;
}

.workspace-card--feature {
  grid-column: span 2;
  background: linear-gradient(180deg, #ebe7de 0%, #e3dfd5 100%);
}

.workspace-card__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.workspace-chip {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border-radius: 999px;
  background: #e9ebe3;
  color: #64675d;
  font-size: 12px;
  font-weight: 700;
}

.workspace-card__eyebrow {
  color: #887d6e;
}

.workspace-card h3 {
  margin: 0;
  color: #28251f;
  font-family: 'Georgia', 'Times New Roman', serif;
  font-size: 28px;
  line-height: 1.24;
  letter-spacing: -0.03em;
}

.workspace-card p,
.empty-note p {
  margin: 12px 0 0;
  color: #696157;
  font-size: 14px;
  line-height: 1.75;
}

.todo-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 22px;
}

.todo-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 16px;
  border: 1px solid #e4e3dc;
  border-radius: 16px;
  background: #f3f0e9;
  text-align: left;
}

.todo-item__icon {
  width: 42px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #e8e4dc;
  color: #62655d;
}

.todo-item__body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.todo-item__body strong {
  color: #28251f;
  font-size: 15px;
}

.todo-item__body small {
  color: #6b665e;
  font-size: 12px;
  line-height: 1.65;
}

.empty-note {
  margin-top: 22px;
  padding: 18px;
  border-radius: 18px;
  background: #efede6;
  border: 1px solid #e1ddd4;
}

.empty-note strong {
  color: #28251f;
  font-size: 15px;
}

.quick-panel {
  padding: 20px;
}

.quick-panel__title {
  margin: 0 0 14px;
  color: #28251f;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
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
  color: #55594f;
  font-size: 13px;
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
  background: #ece7de;
  color: #62655d;
  font-size: 18px;
}

.workspace-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 22px;
  color: #5b6255;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

@media (max-width: 1100px) {
  .welcome-hero,
  .welcome-layout {
    grid-template-columns: 1fr;
  }

  .workspace-card--feature {
    grid-column: span 1;
  }

  .welcome-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 680px) {
  .welcome-hero,
  .workspace-card,
  .quick-panel {
    padding: 20px;
  }

  .welcome-stats,
  .todo-list {
    grid-template-columns: 1fr;
  }

  .workspace-card__head {
    flex-direction: column;
  }
}
</style>
