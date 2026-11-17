/**
 * 统一的错误处理工具函数
 * 提供友好的错误提示信息
 */

/**
 * 从错误对象中提取友好的错误消息
 * @param {Error} error - 错误对象
 * @param {String} defaultMsg - 默认错误消息
 * @param {Object} fieldMap - 字段名称映射（可选）
 * @returns {String} 友好的错误消息
 */
export function getErrorMessage(error, defaultMsg = '操作失败', fieldMap = {}) {
  // 如果没有响应数据，可能是网络错误
  if (!error || !error.response) {
    if (error.message && error.message.includes('timeout')) {
      return '请求超时，请检查网络连接后重试'
    }
    if (error.message && error.message.includes('Network Error')) {
      return '网络连接失败，请检查网络设置'
    }
    return defaultMsg + '，请检查网络连接'
  }

  const response = error.response
  const data = response.data

  if (!data) {
    // HTTP状态码错误
    const statusMessages = {
      400: '请求参数错误，请检查输入',
      401: '未授权，请重新登录',
      403: '没有权限执行此操作',
      404: '请求的资源不存在',
      500: '服务器内部错误，请联系管理员',
      502: '网关错误，请稍后重试',
      503: '服务暂不可用，请稍后重试',
      504: '网关超时，请稍后重试'
    }
    return statusMessages[response.status] || defaultMsg + `（错误代码：${response.status}）`
  }

  // 处理 detail 字段（DRF 标准错误格式）
  if (data.detail) {
    const detail = typeof data.detail === 'string' 
      ? data.detail 
      : (Array.isArray(data.detail) ? data.detail[0] : JSON.stringify(data.detail))
    return detail
  }

  // 处理字段验证错误
  const fieldErrors = []
  const defaultFieldMap = {
    employee: '员工',
    user_id: '工号',
    user_name: '姓名',
    department: '部门',
    position: '岗位',
    work_date: '日期',
    check_in: '上班打卡时间',
    check_out: '下班打卡时间',
    work_hours: '工时',
    overtime_hours: '加班时长',
    start_time: '开始时间',
    end_time: '结束时间',
    leave_type: '请假类型',
    start_date: '开始日期',
    end_date: '结束日期',
    reason: '原因',
    abnormal: '异常说明',
    password: '密码',
    phone: '电话',
    email: '邮箱',
    salary: '薪资',
    performance_score: '绩效分数',
    ...fieldMap
  }

  for (const key in data) {
    if (data.hasOwnProperty(key) && key !== 'non_field_errors' && key !== 'detail' && key !== 'msg') {
      const fieldName = defaultFieldMap[key] || key
      if (Array.isArray(data[key]) && data[key].length > 0) {
        fieldErrors.push(`${fieldName}：${data[key][0]}`)
      } else if (typeof data[key] === 'string' && data[key]) {
        fieldErrors.push(`${fieldName}：${data[key]}`)
      } else if (typeof data[key] === 'object' && data[key] !== null) {
        // 处理嵌套的错误对象
        const nestedErrors = Object.keys(data[key]).map(nestedKey => {
          const nestedFieldName = defaultFieldMap[nestedKey] || nestedKey
          const nestedValue = Array.isArray(data[key][nestedKey]) 
            ? data[key][nestedKey][0] 
            : data[key][nestedKey]
          return `${fieldName}.${nestedFieldName}：${nestedValue}`
        })
        fieldErrors.push(...nestedErrors)
      }
    }
  }

  if (fieldErrors.length > 0) {
    return fieldErrors.length === 1 ? fieldErrors[0] : fieldErrors.join('；')
  }

  // 处理非字段错误
  if (data.non_field_errors) {
    const nonFieldError = Array.isArray(data.non_field_errors) 
      ? data.non_field_errors[0] 
      : data.non_field_errors
    return nonFieldError
  }

  // 处理 msg 字段
  if (data.msg) {
    return data.msg
  }

  // 如果是字符串，直接返回
  if (typeof data === 'string') {
    return data
  }

  // 处理 error 字段
  if (data.error) {
    return typeof data.error === 'string' ? data.error : defaultMsg
  }

  return defaultMsg
}

/**
 * 显示友好的错误消息
 * @param {Error} error - 错误对象
 * @param {String} defaultMsg - 默认错误消息
 * @param {Object} fieldMap - 字段名称映射
 * @param {Function} messageFn - 消息显示函数（默认使用 this.$message.error）
 */
export function showErrorMessage(error, defaultMsg = '操作失败', fieldMap = {}, messageFn = null) {
  const errorMsg = getErrorMessage(error, defaultMsg, fieldMap)
  if (messageFn && typeof messageFn === 'function') {
    messageFn(errorMsg)
  } else {
    // 如果是在Vue组件中使用，需要传入 this.$message.error
    console.error('错误信息：', errorMsg)
    console.error('错误详情：', error)
  }
  return errorMsg
}

