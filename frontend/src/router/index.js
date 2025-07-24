/*Purpose: Configures all application routes and navigation guards. */


import { createRouter, createWebHistory } from 'vue-router';
import { auth } from '../services/api.js';
import LoginView from '../views/LoginView.vue';
import RegisterView from '../views/RegisterView.vue';
import AdminDashboardView from '../views/AdminDashboardView.vue';
import UserDashboardView from '../views/UserDashboardView.vue'; 
import ProfileView from '../views/ProfileView.vue';


const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        { path: '/', redirect: '/login' },
        { path: '/login', name: 'login', component: LoginView },
        { path: '/register', name: 'register', component: RegisterView },
        {
            path: '/admin',
            name: 'admin',
            component: AdminDashboardView,
            meta: { requiresAuth: true, role: 'admin' }
        },
        {
            path: '/dashboard',
            name: 'dashboard',
            component: UserDashboardView,
            meta: { requiresAuth: true, role: 'user' }
        },
        {
            path: '/profile',
            name: 'profile',
            component: ProfileView,
            meta: { requiresAuth: true } 
        }
    ]
});

// Navigation guard to protect routes
router.beforeEach((to, from, next) => {
    const isAuthenticated = !!auth.value.token;
    const userRole = auth.value.role;

    if (to.meta.requiresAuth) {
        if (!isAuthenticated) {
            next({ name: 'login' });
        } else if (to.meta.role && to.meta.role !== userRole) {
            next({ name: 'login' }); 
        } else {
            next();
        }
    } else {
        if (isAuthenticated && (to.name === 'login' || to.name === 'register')) {
            next(userRole === 'admin' ? { name: 'admin' } : { name: 'dashboard' });
        } else {
            next();
        }
    }
});

export default router;