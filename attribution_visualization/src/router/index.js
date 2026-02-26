import { createRouter, createWebHistory } from 'vue-router'
import DetailView from '@/views/TextDetail.vue'
import ImageDetail from '@/views/ImageDetail.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/text',
    },
    {
      path: '/text',
      name: 'text',
      component: DetailView,
    },
    {
      path: '/image',
      name: 'image',
      component: ImageDetail,
    },
  ],
})

export default router
