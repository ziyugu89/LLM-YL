import TabsView from '@/layouts/tabs/TabsView'
// import BlankView from '@/layouts/BlankView'
// import PageView from '@/layouts/PageView'

// 路由配置
const options = {
  routes: [
    {
      path: '/login',
      name: '登录页',
      component: () => import('@/pages/login')
    },
    {
      path: '*',
      name: '404',
      component: () => import('@/pages/exception/404'),
    },
    {
      path: '/403',
      name: '403',
      component: () => import('@/pages/exception/403'),
    },
    {
      path: '/',
      name: '首页',
      component: TabsView,
      redirect: '/login',
      children: [
        {
          path: 'dashboard',
          name: '概览',
          meta: {
            icon: 'dashboard',
          },
          component: () => import('@/pages/dashboard/workplace'),
        },
        {
          path: 'hospital',
          name: '医院实时',
          meta: {
            icon: 'profile',
            authority: {
              role: ['admin', 'use', 'doctor']
            },
          },
          component: () => import('@/pages/hospital'),
        },
        {
          path: 'guide',
          name: '就诊引导',
          meta: {
            icon: 'environment',
            authority: {
              role: ['admin', 'use', 'doctor']
            },
          },
          component: () => import('@/pages/guide'),
        },
        {
          path: 'llm',
          name: '智能导诊',
          meta: {
            icon: 'robot',
            authority: {
              role: ['admin','use']
            },
            page: {
              cacheAble: false
            },
          },
          component: () => import('@/pages/dashboard/llm'),
        },
        {
          path: 'img',
          name: '建立病历',
          meta: {
            icon: 'diff',
            page: {
              cacheAble: false
            },
            authority: {
              role: ['admin', 'doctor']
            },
          },
          component: () => import('@/pages/img/index'),
        },
        {
          path: 'imgbh',
          name: '查看病历',
          meta: {
            icon: 'diff',
            page: {
              cacheAble: false
            },
            authority: {
              role: ['admin', 'use']
            },
          },
          component: () => import('@/pages/imgbh/index'),
        },
        {
          path: 'patients',
          name: '患者查询',
          meta: {
            icon: 'search',
            authority: {
              role: ['admin', 'doctor']
            },
          },
          component: () => import('@/pages/patients'),
        },
        {
          path: 'userSettings',
          name: '医护管理',
          meta: {
            icon: 'user',
            page: {
              cacheAble: false
            },
            authority: {
              role: ['admin']
            },
          },
          component: () => import('@/pages/userSettings/index'),
        },
      ]
    },
  ]
}

export default options
