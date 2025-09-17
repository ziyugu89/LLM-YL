import { LOGIN, ROUTES, GETINFO } from '@/services/api'
import { request, METHOD, removeAuthorization } from '@/utils/request'

/**
 * 登录服务
 * @param name 账户名
 * @param password 账户密码
 * @returns {Promise<AxiosResponse<T>>}
 */
export async function login(name, password) {
  return request(LOGIN, METHOD.POST, {
    username: name,
    password: password
  })
}

/**
 * 获取用户信息
 * @param {*} token 身份临时验证码
 */
export async function getInfo(token) {
  return request(GETINFO, METHOD.GET, { token })
}

export async function getRoutesConfig() {
  return request(ROUTES, METHOD.GET)
}

/**
 * 退出登录
 */
export function logout() {
  logoutRequset().then(({ data }) => {
    if (data.code == 20000) {
      localStorage.removeItem(process.env.VUE_APP_ROUTES_KEY)
      localStorage.removeItem(process.env.VUE_APP_PERMISSIONS_KEY)
      localStorage.removeItem(process.env.VUE_APP_ROLES_KEY)
      removeAuthorization()
    }
  })
}
/**
 * 注销登录
 */
function logoutRequset() {
  return request(
    '/webapi/user/logout',
    METHOD.POST,
    {}
  )
}

export default {
  login,
  logout,
  getRoutesConfig,
  getInfo
}
