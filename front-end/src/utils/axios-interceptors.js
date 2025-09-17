import Cookie from 'js-cookie'
// 401拦截
const resp401 = {
  /**
   * 响应数据之前做点什么
   * @param response 响应对象
   * @param options 应用配置 包含: {router, i18n, store, message}
   * @returns {*}
   */
  onFulfilled(response, options) {
    const { message } = options
    if (response.code === 401) {
      message.error('无此权限')
    }
    return response
  },
  /**
   * 响应出错时执行
   * @param error 错误对象
   * @param options 应用配置 包含: {router, i18n, store, message}
   * @returns {Promise<never>}
   */
  onRejected(error, options) {
    const { message } = options
    const { response } = error
    if (response.status === 401) {
      message.error('无此权限')
    }
    return Promise.reject(error)
  }
}

const resp403 = {
  onFulfilled(response, options) {
    const { message } = options
    if (response.code === 403) {
      message.error('请求被拒绝')
    }
    return response
  },
  onRejected(error, options) {
    const { message } = options
    const { response } = error
    if (response.status === 403) {
      message.error('请求被拒绝')
    }
    return Promise.reject(error)
  }
}

const tokenOut = {
  onFulfilled(response, options) {
    const { message, router } = options
    if (response.data.code === 20001 && (response.data.data === '登录超时' || response.data.data === '请重新登录')) {
      message.error('身份信息到期，请重新登录')
      router.push({ path: '/login' })
      return Promise.reject(new Error(response.data.data || 'Error'))
    } else if (response.data.code === 20001) {
      message.error(response.data.data)
      return Promise.reject(new Error(response.data.data || 'Error'))
    }
    return response
  }
}

const reqCommon = {
  /**
   * 发送请求之前做些什么
   * @param config axios config
   * @param options 应用配置 包含: {router, i18n, store, message}
   * @returns {*}
   */
  onFulfilled(config, options) {
    const { message, router } = options
    const { url, xsrfCookieName } = config
    if (url.indexOf('login') === -1 && url.indexOf('/webapi/user/info') === -1 && url.indexOf('/webapi/user/adduser') === -1 && xsrfCookieName && !Cookie.get(xsrfCookieName)) {
      message.warning('认证 token 已过期，请重新登录')
      router.push({ path: '/login' })
      return Promise.reject(new Error(config.data.data || 'Error'))
    }
    return config
  },
  /**
   * 请求出错时做点什么
   * @param error 错误对象
   * @param options 应用配置 包含: {router, i18n, store, message}
   * @returns {Promise<never>}
   */
  onRejected(error, options) {
    const { message } = options
    message.error(error.message)
    return Promise.reject(error)
  }
}

export default {
  request: [reqCommon], // 请求拦截
  response: [resp401, resp403, tokenOut] // 响应拦截
}
