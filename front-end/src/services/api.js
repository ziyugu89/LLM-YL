//跨域代理前缀
// const API_PROXY_PREFIX='/api'
// const BASE_URL = process.env.NODE_ENV === 'production' ? process.env.VUE_APP_API_BASE_URL : API_PROXY_PREFIX
// const BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://127.0.0.1'
module.exports = {
  LOGIN: `/webapi/user/login`,
  ROUTES: `/routes`,


  GETINFO: `/webapi/user/info`,
}
