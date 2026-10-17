import { request, METHOD } from '@/utils/request'

/**
 * 查询用户列表
 * @param {*} data {limit,page}
 */
export async function getList(data) {
  return request(
    '/webapi/user/getlist',
    METHOD.POST,
    data
  )
}
/**
 * 创建用户
 * @param {*} data 
 */
export async function addUser(data) {
  return request(
    '/webapi/user/adduser',
    METHOD.POST,
    data
  )
}
/**
 * 修改用户
 * @param {*} data 
 */
export function upUser(data) {
  return request(
    '/webapi/user/upUser',
    METHOD.POST,
    data
  )
}
// 用户除权
export function delUser(data) {
  return request(
    '/webapi/user/delUser',
    METHOD.POST,
    data
  )
}
// 通过token修改密码
export function upUserPwd(data) {
  return request(
    '/webapi/user/upUserPwd',
    METHOD.POST,
    data
  )
}
// 添加病历
export function addbingli(data) {
  return request(
    '/webapi/data/addbingli',
    METHOD.POST,
    data
  )
}
// 获取病历
export function getbingli(data) {
  return request(
    '/webapi/data/getbingli',
    METHOD.POST,
    data
  )
}
// 获取病历
export function llm(data) {
  return request(
    '/webapi/data/llm',
    METHOD.POST,
    data
  )
}
export function hospital(data) {
  return request(
    '/webapi/data/hospital',
    METHOD.POST,
    data
  )
}
export function guide(data) {
  return request(
    '/webapi/data/guide',
    METHOD.POST,
    data
  )
}
// 添加提醒
export function setmessage(data) {
  return request(
    '/webapi/data/setmessage',
    METHOD.POST,
    data
  )
}
// 获取提醒
export function getmessage(data) {
  return request(
    '/webapi/data/getmessage',
    METHOD.POST,
    data
  )
}
// 病患病历查看
export function getbingliBH(data) {
  return request(
    '/webapi/data/getbingliBH',
    METHOD.POST,
    data
  )
}