/**
 * Excel导出工具函数
 * 通过动态加载 xlsx，避免首屏同步打包导出库。
 */
let xlsxLoader = null

function loadXLSX() {
  if (!xlsxLoader) {
    xlsxLoader = import('xlsx')
      .then((mod) => (mod && mod.default ? mod.default : mod))
      .catch((error) => {
        xlsxLoader = null
        throw error
      })
  }
  return xlsxLoader
}

function createExportError(message, originalError = null) {
  const error = new Error(message)
  if (originalError) {
    error.originalError = originalError
  }
  return error
}

function normalizeExportConfig(data, columns, filename) {
  if (Array.isArray(columns)) {
    return { columns, filename }
  }

  const inferredFilename = typeof columns === 'string' ? columns : filename
  const firstRow = data && data[0] ? data[0] : {}
  const inferredColumns = Object.keys(firstRow).map((key) => ({
    key,
    label: key,
  }))

  return {
    columns: inferredColumns,
    filename: inferredFilename || '导出数据',
  }
}

/**
 * 导出数据为 Excel 文件
 * @param {Array} data - 要导出的数据数组
 * @param {Array} columns - 列配置数组，格式: [{key: '字段名', label: '列标题'}]
 * @param {String} filename - 文件名（不含扩展名）
 * @param {String} sheetName - 工作表名称，默认 Sheet1
 */
export function exportToExcel(data, columns, filename = '导出数据', sheetName = 'Sheet1') {
  if (!data || data.length === 0) {
    return Promise.reject(createExportError('暂无可导出的数据'))
  }

  const exportConfig = normalizeExportConfig(data, columns, filename)
  const normalizedColumns = exportConfig.columns
  const normalizedFilename = exportConfig.filename

  if (!normalizedColumns || normalizedColumns.length === 0) {
    return Promise.reject(createExportError('暂无可导出的字段'))
  }

  return loadXLSX()
    .then((XLSX) => {
      try {
        const worksheetData = []

        const headers = normalizedColumns.map((col) => col.label)
        worksheetData.push(headers)

        data.forEach((row) => {
          const rowData = normalizedColumns.map((col) => {
            const value = row[col.key]
            if (value === null || value === undefined) {
              return ''
            }
            if (typeof value === 'object') {
              return JSON.stringify(value)
            }
            return value
          })
          worksheetData.push(rowData)
        })

        const workbook = XLSX.utils.book_new()
        const worksheet = XLSX.utils.aoa_to_sheet(worksheetData)

        const colWidths = normalizedColumns.map(() => ({ wch: 15 }))
        worksheet['!cols'] = colWidths

        const outputFilename = `${normalizedFilename}_${new Date().getTime()}.xlsx`
        XLSX.utils.book_append_sheet(workbook, worksheet, sheetName)
        XLSX.writeFile(workbook, outputFilename)

        return {
          filename: outputFilename,
          count: data.length,
        }
      } catch (error) {
        throw createExportError(error && error.message ? error.message : '导出过程发生异常', error)
      }
    })
    .catch((error) => {
      const message = error && error.message ? error.message : '导出组件加载失败'
      const friendlyMessage = message.includes('Loading chunk') || message.includes('Cannot find module') || message.includes('Failed to fetch')
        ? '导出组件加载失败'
        : message
      console.error('导出失败:', error)
      throw createExportError(friendlyMessage, error)
    })
}

/**
 * 导出表格数据（从 Element UI 表格组件）
 * @param {Array} tableData - 表格数据
 * @param {Array} tableColumns - Element UI 表格列配置
 * @param {String} filename - 文件名
 */
export function exportTableToExcel(tableData, tableColumns, filename = '导出数据') {
  if (!tableData || tableData.length === 0) {
    console.warn('没有数据可导出')
    return
  }

  const columns = tableColumns
    .filter((col) => col.prop && col.label)
    .map((col) => ({
      key: col.prop,
      label: col.label,
    }))

  return exportToExcel(tableData, columns, filename)
}

/**
 * 导出多个工作表
 * @param {Array} sheets - 工作表配置数组，格式: [{name: '工作表名', data: [], columns: []}]
 * @param {String} filename - 文件名
 */
export function exportMultipleSheets(sheets, filename = '导出数据') {
  if (!sheets || sheets.length === 0) {
    console.warn('没有工作表可导出')
    return
  }

  loadXLSX()
    .then((XLSX) => {
      const workbook = XLSX.utils.book_new()

      sheets.forEach((sheet) => {
        const { name, data, columns } = sheet

        if (!data || data.length === 0) {
          console.warn(`工作表 ${name} 没有数据`)
          return
        }

        const worksheetData = []

        const headers = columns.map((col) => col.label)
        worksheetData.push(headers)

        data.forEach((row) => {
          const rowData = columns.map((col) => {
            const value = row[col.key]
            if (value === null || value === undefined) {
              return ''
            }
            if (typeof value === 'object') {
              return JSON.stringify(value)
            }
            return value
          })
          worksheetData.push(rowData)
        })

        const worksheet = XLSX.utils.aoa_to_sheet(worksheetData)

        const colWidths = columns.map(() => ({ wch: 15 }))
        worksheet['!cols'] = colWidths

        XLSX.utils.book_append_sheet(workbook, worksheet, name || 'Sheet1')
      })

      XLSX.writeFile(workbook, `${filename}_${new Date().getTime()}.xlsx`)
    })
    .catch((error) => {
      console.error('加载导出模块失败:', error)
    })
}
