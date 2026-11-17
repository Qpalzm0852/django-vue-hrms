<template>
  <div class="bg-surface min-h-screen flex flex-col items-center justify-center overflow-hidden antialiased login-page">
    <div class="fixed top-0 left-0 w-full h-full pointer-events-none z-0">
      <div class="absolute -top-[10%] -right-[5%] w-1/3 h-2/3 bg-primary/5 rounded-full blur-[120px]"></div>
      <div class="absolute -bottom-[10%] -left-[5%] w-1/4 h-1/2 bg-secondary/5 rounded-full blur-[100px]"></div>
    </div>

    <main class="relative z-10 w-full max-w-md px-6 lg:px-0">
      <div class="mb-10 text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-primary-container editorial-shadow mb-6">
          <i class="el-icon-office-building text-white text-3xl"></i>
        </div>
        <h1 class="text-2xl font-black text-primary tracking-tighter mb-2">企业人力资源管理系统 (HRMS)</h1>
        <p class="text-on-surface-variant font-medium tracking-tight text-sm">
          统一管理员工、组织、考勤与薪酬流程
        </p>
      </div>

      <div class="bg-surface-container-lowest editorial-shadow rounded-xl p-8 lg:p-10 border border-outline-variant/15">
        <form class="space-y-6" @submit.prevent="loginIn">
          <div class="space-y-2">
            <label class="block text-[11px] font-bold text-on-surface-variant uppercase tracking-widest" for="login-user-id">
              账号 / 工号
            </label>
            <div class="relative group">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <i class="el-icon-user text-outline text-lg transition-colors group-focus-within:text-secondary"></i>
              </div>
              <input
                id="login-user-id"
                v-model="loginForm.user_id"
                class="block w-full pl-12 pr-4 py-3 bg-surface-container-low border border-outline-variant/20 rounded-lg text-primary text-sm focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all"
                autocomplete="username"
                placeholder="请输入管理员账号或员工工号"
                type="text"
                @keyup.enter="loginIn"
              />
            </div>
          </div>

          <div class="space-y-2">
            <div class="flex justify-between items-end">
              <label class="block text-[11px] font-bold text-on-surface-variant uppercase tracking-widest" for="login-password">密码</label>
              <span class="text-[11px] font-bold text-secondary uppercase tracking-widest">
                忘记密码请联系管理员
              </span>
            </div>
            <div class="relative group">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <i class="el-icon-lock text-outline text-lg transition-colors group-focus-within:text-secondary"></i>
              </div>
              <input
                id="login-password"
                v-model="loginForm.password"
                class="block w-full pl-12 pr-12 py-3 bg-surface-container-low border border-outline-variant/20 rounded-lg text-primary text-sm focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all"
                autocomplete="current-password"
                placeholder="请输入登录密码"
                :type="passwordVisible ? 'text' : 'password'"
                @keyup.enter="loginIn"
              />
              <div class="absolute inset-y-0 right-0 pr-4 flex items-center">
                <button
                  class="text-outline hover:text-primary transition-colors"
                  type="button"
                  :aria-label="passwordVisible ? '隐藏密码' : '显示密码'"
                  @click="passwordVisible = !passwordVisible"
                >
                  <i :class="passwordVisible ? 'el-icon-circle-close text-lg' : 'el-icon-view text-lg'"></i>
                </button>
              </div>
            </div>
          </div>

          <div class="flex items-center">
            <div class="flex items-center h-5">
              <input
                id="remember"
                v-model="rememberMe"
                class="w-4 h-4 text-secondary bg-surface-container-low border-outline-variant/30 rounded focus:ring-secondary transition-all cursor-pointer"
                type="checkbox"
              />
            </div>
            <label class="ml-3 text-xs font-medium text-on-surface-variant cursor-pointer select-none" for="remember">
              30 天内记住当前账号
            </label>
          </div>

          <button
            class="w-full btn-gradient text-white font-bold py-4 rounded-lg shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all duration-200 tracking-tight text-sm disabled:cursor-not-allowed disabled:opacity-70"
            type="submit"
            :disabled="loading"
          >
            {{ loading ? '正在登录...' : '进入系统工作台' }}
          </button>
        </form>

        <div class="mt-8 pt-8 border-t border-outline-variant/10">
          <div class="flex items-center justify-between">
            <p class="text-xs text-on-surface-variant">系统连接状态</p>
            <div class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-secondary"></span>
              <span class="text-[10px] font-bold text-secondary uppercase tracking-wider">安全连接正常</span>
            </div>
          </div>
        </div>
      </div>

      <p class="mt-8 text-center text-xs text-on-surface-variant px-6">
        首次入职或账号未开通时，请联系 <span class="font-bold text-primary">人事管理员</span> 初始化权限。
      </p>
    </main>

    <footer class="w-full py-4 mt-auto border-t border-slate-200/50 bg-slate-50 flex justify-between items-center px-8">
      <div class="flex items-center space-x-6">
        <span class="font-inter text-[11px] uppercase tracking-widest text-slate-500">
          (c) 2024 Enterprise HRMS. All rights reserved.
        </span>
      </div>
      <div class="flex space-x-6 items-center">
        <a class="font-inter text-[11px] uppercase tracking-widest text-slate-400 hover:text-[#2d5a27] transition-colors opacity-80 hover:opacity-100" href="#" @click.prevent>Privacy</a>
        <a class="font-inter text-[11px] uppercase tracking-widest text-slate-400 hover:text-[#2d5a27] transition-colors opacity-80 hover:opacity-100" href="#" @click.prevent>Terms</a>
        <span class="font-inter text-[11px] uppercase tracking-widest text-slate-400 opacity-50">v2.4.0-pro</span>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  data() {
    return {
      loginForm: {
        user_id: '',
        password: '',
      },
      passwordVisible: false,
      rememberMe: false,
      loading: false,
      loginFormRules: {
        user_id: [
          { required: true, message: '请输入工号/账号', trigger: 'blur' },
          { min: 3, max: 20, message: '长度应为 3-20 个字符', trigger: 'blur' },
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, max: 20, message: '长度应为 6-20 个字符', trigger: 'blur' },
        ],
      },
    }
  },
  mounted() {
    const rememberedUserId = localStorage.getItem('remembered_user_id')
    if (rememberedUserId) {
      this.loginForm.user_id = rememberedUserId
      this.rememberMe = true
    }
  },
  methods: {
    validateLoginForm() {
      if (!this.loginForm.user_id) {
        this.$message.error('请输入工号/账号')
        return false
      }
      if (this.loginForm.user_id.length < 3 || this.loginForm.user_id.length > 20) {
        this.$message.error('账号长度应为 3-20 个字符')
        return false
      }
      if (!this.loginForm.password) {
        this.$message.error('请输入密码')
        return false
      }
      if (this.loginForm.password.length < 6 || this.loginForm.password.length > 20) {
        this.$message.error('密码长度应为 6-20 个字符')
        return false
      }
      return true
    },
    async loginIn() {
      if (!this.validateLoginForm()) return

      this.loading = true
      try {
        const { data: res } = await this.$http.post('login/', this.loginForm)

        const statusCode = Number(res && res.status ? res.status : 200)
        const payload = res && res.data ? res.data : res
        const token = payload && payload.token
        const userId = payload && payload.user_id
        const userName = payload && payload.user_name
        const role = payload && payload.role

        if (statusCode !== 200 || !token || !userId || !role) {
          this.$message.error(this.extractLoginError(res) || '登录失败，请检查账号和密码')
          return
        }

        if (this.rememberMe) {
          localStorage.setItem('remembered_user_id', this.loginForm.user_id)
        } else {
          localStorage.removeItem('remembered_user_id')
        }

        window.sessionStorage.setItem('token', token)
        window.sessionStorage.setItem('user', userId)
        window.sessionStorage.setItem('user_name', userName || userId)
        window.sessionStorage.setItem('role', role)

        this.$message.success('登录成功')

        if (role === 'ADMIN' || role === 'HR' || role === 'MANAGER') {
          this.$router.push('/admin/home')
        } else if (role === 'STAFF') {
          this.$router.push('/employee/home')
        } else {
          this.$message.error('未知用户角色，请联系管理员')
        }
      } catch (error) {
        console.error('登录请求失败:', error)
        this.$message.error(this.getErrorMessage(error, '登录请求失败'))
      } finally {
        this.loading = false
      }
    },
    extractLoginError(res) {
      if (!res) return ''
      if (typeof res === 'string') return res
      const detail = res.detail || (res.data && res.data.detail)
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail) && detail.length) return detail[0]
      if (detail && typeof detail === 'object') {
        const firstKey = Object.keys(detail)[0]
        const firstValue = detail[firstKey]
        if (Array.isArray(firstValue) && firstValue.length) return firstValue[0]
      }
      return ''
    },
    getErrorMessage(error, defaultMsg) {
      const data = error && error.response && error.response.data
      if (!data) {
        return defaultMsg + '，请检查后端服务是否启动'
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

<style scoped>
.login-page {
  font-family: 'Inter', sans-serif;
}

.editorial-shadow {
  box-shadow: 0 12px 32px rgba(26, 43, 60, 0.06);
}

.btn-gradient {
  background: linear-gradient(135deg, #041627 0%, #1a2b3c 100%);
}

@media (max-width: 640px) {
  footer {
    padding-left: 1rem;
    padding-right: 1rem;
    gap: 0.75rem;
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
