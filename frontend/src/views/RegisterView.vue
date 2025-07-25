<template>
    <div class="row justify-content-center">
        <div class="col-md-6 col-lg-4">
            <div class="card shadow-lg border-0 p-4">
                <h2 class="text-center mb-4">Create an Account</h2>
                <div v-if="error" class="alert alert-danger">{{ error }}</div>
                <div v-if="success" class="alert alert-success">{{ success }}</div>
                <form @submit.prevent="handleRegister">
                    <div class="mb-3">
                        <label class="form-label">Username</label>
                        <input type="text" v-model="form.username" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Email</label>
                        <input type="email" v-model="form.email" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" v-model="form.password" class="form-control" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100" :disabled="loading">
                         <span v-if="loading" class="spinner-border spinner-border-sm"></span>
                        <span v-else>Register</span>
                    </button>
                </form>
                 <div class="text-center mt-3">
                    <router-link to="/login">Already have an account? Login</router-link>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { apiRequest } from '../services/api.js';

const form = ref({ username: '', email: '', password: '' });
const error = ref(null);
const success = ref(null);
const loading = ref(false);
const router = useRouter();

const handleRegister = async () => {
    error.value = null;
    success.value = null;
    loading.value = true;
    try {
        const data = await apiRequest('/register', 'POST', form.value);
        success.value = `${data.msg}! Redirecting to login...`;
        setTimeout(() => router.push('/login'), 2000);
    } catch (err) {
        error.value = err.message;
    } finally {
        loading.value = false;
    }
};
</script>