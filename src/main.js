import Vue from 'vue'
import App from './App.vue'
import router from './router'
import './plugins/element.js'
import './assets/css/global.css'

import axios from 'axios'

axios.defaults.baseURL = 'http://127.0.0.1:8001/'
let isAuthRedirecting = false
let lastGlobalErrorMessage = ''
let lastGlobalErrorTime = 0

function showGlobalError(message) {
  const now = Date.now()
  if (message === lastGlobalErrorMessage && now - lastGlobalErrorTime < 1500) {
    return
  }
  lastGlobalErrorMessage = message
  lastGlobalErrorTime = now
  Vue.prototype.$message.error(message)
}

axios.interceptors.request.use((config) => {
  const token = window.sessionStorage.getItem('token')
  const requestUrl = (config.url || '').toString()
  const isLoginRequest = requestUrl.includes('/login/') || requestUrl === 'login/' || requestUrl === '/login'

  if (!isLoginRequest && token && token !== 'null' && token !== 'undefined') {
    config.headers.authorization = 'jwt ' + token
  } else if (config.headers && config.headers.authorization) {
    delete config.headers.authorization
  }

  return config
})

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error && error.response ? Number(error.response.status) : 0
    if (status === 401) {
      showGlobalError('登录状态已失效，请重新登录')
    } else if (status === 403) {
      showGlobalError('当前账号无权限访问该功能')
    } else if (status >= 500) {
      showGlobalError('服务器异常，请稍后重试')
    } else if (!error.response) {
      showGlobalError('网络连接异常，请检查后重试')
    }

    if (status === 401 || status === 403) {
      if (!isAuthRedirecting) {
        isAuthRedirecting = true
        window.sessionStorage.clear()
        const currentPath = (router.currentRoute && router.currentRoute.path) || ''
        if (currentPath !== '/login') {
          router.replace('/login').catch(() => {})
        }
        setTimeout(() => {
          isAuthRedirecting = false
        }, 1000)
      }
    }
    return Promise.reject(error)
  }
)

Vue.prototype.$http = axios
Vue.config.productionTip = false

new Vue({
  router,
  render: (h) => h(App),
}).$mount('#app')
