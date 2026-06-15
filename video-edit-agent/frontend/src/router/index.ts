import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/project',
    name: 'Project',
    component: () => import('../views/ProjectView.vue'),
  },
  {
    path: '/config',
    name: 'Config',
    component: () => import('../views/ConfigView.vue'),
  },
  {
    path: '/batch',
    name: 'Batch',
    component: () => import('../views/BatchView.vue'),
  },
  {
    path: '/batch/:batchId',
    name: 'BatchDetail',
    component: () => import('../views/BatchView.vue'),
  },
  {
    path: '/transcode',
    name: 'Transcode',
    component: () => import('../views/TranscodeView.vue'),
  },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
