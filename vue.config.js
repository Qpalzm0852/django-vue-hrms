module.exports = {
  productionSourceMap: false,
  chainWebpack: (config) => {
    // 关闭默认 prefetch，避免对大量异步 chunk 进行提前预取
    config.plugins.delete('prefetch')
  },
}
