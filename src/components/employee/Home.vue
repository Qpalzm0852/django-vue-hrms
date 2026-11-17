<template>
  <div class="text-on-surface antialiased hr-shell">
    <div v-if="sidebarOpen" class="fixed inset-0 z-40 bg-slate-950/35 lg:hidden" @click="closeSidebar"></div>

    <aside
      class="fixed left-0 top-0 h-screen w-64 z-50 bg-[#1a2b3c] flex flex-col py-6 space-y-2 text-sm font-medium shadow-2xl shadow-slate-900/20 transition-transform duration-300 lg:translate-x-0"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <div class="px-6 mb-8 flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center">
          <span class="material-symbols-outlined text-white" style="font-variation-settings: 'FILL' 1">badge</span>
        </div>
        <div>
          <h1 class="text-lg font-bold text-white tracking-tight">Employee Hub</h1>
          <p class="text-[10px] tracking-widest text-slate-400">员工自助服务</p>
        </div>
      </div>

      <nav class="flex-1 px-2 space-y-4 overflow-y-auto no-scrollbar">
        <section v-for="group in navGroups" :key="group.label" class="space-y-1">
          <p class="px-4 text-[10px] tracking-[0.2em] text-slate-500 uppercase font-bold">{{ group.label }}</p>
          <button
            v-for="item in group.items"
            :key="item.path"
            type="button"
            class="w-[calc(100%-1rem)] text-left px-4 py-3 mx-2 rounded-md flex items-center gap-3 transition-all duration-200"
            :class="
              activePath === item.path
                ? 'bg-white/10 backdrop-blur-md text-white border-l-4 border-[#3b6934]'
                : 'text-slate-300 hover:text-white hover:bg-white/5'
            "
            @click="goToMenu(item.path)"
          >
            <span class="material-symbols-outlined text-[20px]">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </button>
        </section>
      </nav>

      <div class="mt-auto px-4 pt-4 border-t border-white/10 flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-white/10 border border-white/10 flex items-center justify-center text-white text-xs font-bold">
          {{ userInitials }}
        </div>
        <div class="overflow-hidden">
          <p class="text-white text-xs font-bold truncate">{{ userName }}</p>
          <p class="text-slate-400 text-[10px] truncate">员工工作台</p>
        </div>
      </div>
    </aside>

    <main class="min-h-screen flex flex-col lg:ml-64">
      <header class="fixed top-0 right-0 left-0 lg:left-64 z-40 h-16 bg-white flex items-center justify-between px-4 lg:px-8 shadow-[0_2px_10px_rgba(26,43,60,0.04)] tracking-tight">
        <div class="flex items-center flex-1 min-w-0 gap-3 max-w-xl">
          <button class="inline-flex lg:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors" type="button" aria-label="打开导航菜单" @click="toggleSidebar">
            <span class="material-symbols-outlined">menu</span>
          </button>
          <div class="relative flex-1 min-w-0">
            <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-lg">search</span>
            <input
              class="w-full bg-slate-50 border-none rounded-lg pl-10 pr-4 py-2 text-sm focus:ring-2 focus:ring-secondary/20 transition-all"
              v-model.trim="searchQuery"
              placeholder="搜索工资、公告、培训或个人档案..."
              type="text"
              @focus="searchOpen = true"
              @keydown.enter.prevent="goToSearchResult(searchResults[0])"
            />
            <div v-if="searchOpen && searchQuery" class="search-panel">
              <button
                v-for="item in searchResults"
                :key="item.path"
                type="button"
                class="search-panel__item"
                @mousedown.prevent="goToSearchResult(item)"
              >
                <span class="search-panel__group">{{ item.group }}</span>
                <strong>{{ item.label }}</strong>
              </button>
              <div v-if="!searchResults.length" class="search-panel__empty">没有找到匹配入口</div>
            </div>
          </div>
        </div>

        <div class="flex items-center flex-shrink-0 gap-2 lg:gap-4">
          <button class="hidden sm:inline-flex p-2 text-slate-500 hover:bg-slate-50 rounded-full transition-all active:scale-95 duration-200" type="button" aria-label="通知中心">
            <span class="material-symbols-outlined">notifications</span>
          </button>
          <div class="hidden sm:block h-8 w-px bg-slate-200 mx-2"></div>
          <div class="flex items-center gap-2 lg:gap-3">
            <div class="hidden md:block text-right max-w-[132px] lg:max-w-[160px] overflow-hidden">
              <p class="text-sm font-bold text-[#1a2b3c] truncate">{{ userName }}</p>
              <p class="text-[10px] text-slate-400 tracking-widest truncate">个人工作台</p>
            </div>
            <div class="w-9 h-9 rounded-full bg-slate-100 text-[#1a2b3c] flex items-center justify-center text-xs font-bold ring-2 ring-transparent hover:ring-secondary/30 transition-all">
              {{ userInitials }}
            </div>
            <button
              class="inline-flex flex-shrink-0 items-center gap-1 px-3 py-2 rounded-lg bg-primary text-white text-xs font-semibold whitespace-nowrap hover:bg-primary-container transition-colors"
              type="button"
              @click="logout"
            >
              <span class="material-symbols-outlined text-base">logout</span>
              <span>退出</span>
            </button>
          </div>
        </div>
      </header>

      <div class="mt-16 p-4 lg:p-8 flex-1">
        <router-view></router-view>
      </div>

      <footer class="w-full py-4 mt-auto flex flex-col gap-2 lg:flex-row lg:justify-between lg:items-center px-4 lg:px-8 border-t border-slate-100 bg-slate-50 text-[11px] tracking-widest text-slate-500">
        <div>(c) 2024 企业人力资源管理系统。版权所有。</div>
        <div class="flex gap-4 lg:gap-6 flex-wrap">
          <a class="hover:text-[#2d5a27] transition-colors" href="#" @click.prevent>隐私政策</a>
          <a class="hover:text-[#2d5a27] transition-colors" href="#" @click.prevent>服务条款</a>
          <span class="text-slate-400">employee-portal</span>
        </div>
      </footer>
    </main>
  </div>
</template>

<script>
export default {
  data() {
    return {
      sidebarOpen: false,
      activePath: '',
      userName: '员工',
      searchQuery: '',
      searchOpen: false,
      navGroups: [
        {
          label: '总览',
          items: [
            { label: '首页概览', icon: 'space_dashboard', path: '/employee/welcome' },
            { label: '公告中心', icon: 'campaign', path: '/employee/announcement' },
          ],
        },
        {
          label: '我的工作',
          items: [
            { label: '我的工资条', icon: 'receipt_long', path: '/employee/payroll' },
            { label: '我的考勤', icon: 'event_available', path: '/employee/attendance' },
            { label: '请假申请', icon: 'event_busy', path: '/employee/leave' },
            { label: '加班申请', icon: 'schedule', path: '/employee/overtime' },
          ],
        },
        {
          label: '成长记录',
          items: [
            { label: '我的绩效', icon: 'query_stats', path: '/employee/performance' },
            { label: '我的培训', icon: 'school', path: '/employee/training' },
          ],
        },
        {
          label: '个人信息',
          items: [
            { label: '个人档案', icon: 'badge', path: '/employee/profile' },
          ],
        },
      ],
    }
  },
  computed: {
    searchResults() {
      const keyword = (this.searchQuery || '').toLowerCase()
      if (!keyword) return []
      return this.navGroups
        .flatMap((group) =>
          group.items.map((item) => ({
            ...item,
            group: group.label,
          }))
        )
        .filter((item) => item.label.toLowerCase().includes(keyword) || item.group.toLowerCase().includes(keyword))
        .slice(0, 6)
    },
    userInitials() {
      const source = (this.userName || '').trim()
      if (!source) return 'YG'
      return source.slice(0, 2).toUpperCase()
    },
  },
  created() {
    this.activePath = window.sessionStorage.getItem('activePath') || '/employee/welcome'
    this.userName = window.sessionStorage.getItem('user_name') || '员工'
    document.addEventListener('click', this.handleDocumentClick)
  },
  beforeDestroy() {
    document.removeEventListener('click', this.handleDocumentClick)
  },
  watch: {
    $route: {
      immediate: true,
      handler(route) {
        this.activePath = route.path
        window.sessionStorage.setItem('activePath', route.path)
        this.sidebarOpen = false
      },
    },
  },
  methods: {
    logout() {
      window.sessionStorage.clear()
      this.$router.push('/login')
    },
    toggleSidebar() {
      this.sidebarOpen = !this.sidebarOpen
    },
    closeSidebar() {
      this.sidebarOpen = false
    },
    saveNavState(activePath) {
      window.sessionStorage.setItem('activePath', activePath)
      this.activePath = activePath
    },
    handleDocumentClick(event) {
      const target = event.target
      if (!(target instanceof HTMLElement)) return
      if (!target.closest('.relative.w-full')) {
        this.searchOpen = false
      }
    },
    goToSearchResult(item) {
      if (!item) return
      this.searchQuery = ''
      this.searchOpen = false
      this.goToMenu(item.path)
    },
    goToMenu(path) {
      this.saveNavState(path)
      if (this.$route.path !== path) {
        this.$router.push(path)
      }
    },
  },
}
</script>

<style scoped>
.hr-shell {
  font-family: 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', 'Noto Sans SC', 'Inter', sans-serif;
  background: linear-gradient(180deg, #e8ebe6 0%, #f2f1ed 100%);
}

.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}

.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.search-panel {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  z-index: 60;
  padding: 8px;
  border: 1px solid #dbe4ec;
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 18px 30px rgba(15, 32, 52, 0.12);
}

.search-panel__item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border: none;
  border-radius: 10px;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.search-panel__item:hover {
  background: #f5f8fb;
}

.search-panel__group {
  color: #789;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.search-panel__item strong {
  color: #193047;
  font-size: 13px;
}

.search-panel__empty {
  padding: 12px;
  color: #7a8896;
  font-size: 13px;
}
</style>
