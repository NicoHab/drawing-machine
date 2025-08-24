import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    // Redirect any other routes to home
    {
      path: '/:pathMatch(.*)*',
      redirect: '/'
    }
  ],
})

export default router
