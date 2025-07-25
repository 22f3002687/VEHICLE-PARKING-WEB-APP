<template>
    <div class="d-flex align-items-center justify-content-center" style="min-height: 75vh;">
        <div class="row justify-content-center w-100">
            <div class="col-11 col-sm-10 col-md-8 col-lg-6 col-xl-5 col-xxl-4">
                <div class="card shadow-lg border-0 p-4">
                    <h2 class="text-center mb-4">Login</h2>
                    <div v-if="error" class="alert alert-danger">{{ error }}</div>
                    <form @submit.prevent="handleLogin">
                        <div class="mb-3">
                            <label class="form-label">Username</label>
                            <input type="text" v-model="username" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Password</label>
                            <input type="password" v-model="password" class="form-control" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100" :disabled="loading">
                         <span v-if="loading" class="spinner-border spinner-border-sm"></span>
                        <span v-else>Login</span>
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { apiRequest, login as authLogin } from '../services/api.js';

const username = ref('');
const password = ref('');
const error = ref(null);
const loading = ref(false);
const router = useRouter();


const handleLogin = async () => {
    error.value = null;
    loading.value = true;
    try {
        const data = await apiRequest('/login', 'POST', {
            username: username.value,
            password: password.value,
        });
        authLogin(data.access_token, data.role, data.username);
        router.push(data.role === 'admin' ? '/admin' : '/dashboard');
    } catch (err) {
        error.value = err.message;
    } finally {
        loading.value = false;
    }
};
</script>