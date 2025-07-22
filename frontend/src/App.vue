/*Purpose: The main application shell with navbar and router.*/


<template>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm">
        <div class="container-fluid">
            <router-link class="navbar-brand" to="/"><i class="bi bi-p-circle-fill"></i> Parking Pro</router-link>
            <div class="d-flex">
                <div v-if="!auth.token" class="d-flex">
                    <router-link to="/login" class="btn btn-outline-light me-2">Login</router-link>
                    <router-link to="/register" class="btn btn-light">Register</router-link>
                </div>
                <div v-if="auth.token" class="d-flex align-items-center">
                    <span class="navbar-text me-3 text-white">Welcome, <strong>{{ auth.username }}</strong> ({{ auth.role }})</span>
                    <button @click="handleLogout" class="btn btn-outline-warning">Logout</button>
                </div>
            </div>
        </div>
    </nav>
    <main class="container mt-4">
        <router-view />
    </main>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { auth, logout } from './services/api.js';

const router = useRouter();

const handleLogout = () => {
    logout();
    router.push('/login');
};
</script>

<style>
@import "https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css";
@import "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css";

body {
    background-color: #f0f2f5;
}
</style>

