import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import VisitorView from '../views/VisitorView.vue'
import AdminControlView from '../views/AdminControlView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView, // Redirects to visitor
    },
    {
      path: '/visitor',
      name: 'visitor',
      component: VisitorView,
    },
    {
      path: '/display', 
      name: 'display',
      component: VisitorView, // Same as visitor
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminControlView,
    },
    {
      path: '/control',
      name: 'control', 
      component: AdminControlView, // Same as admin
    },
    // Redirect any other routes to visitor
    {
      path: '/:pathMatch(.*)*',
      redirect: '/visitor'
    }
  ],
})

export default router
