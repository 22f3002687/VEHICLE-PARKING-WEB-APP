/*Purpose: Displays the profile information for the logged-in user*/
<template>
    <div class="container my-4">
        <div class="row justify-content-center">
            <div class="col-md-8 col-lg-6">
                <div class="card shadow-sm">
                    <div class="card-header bg-dark text-white">
                        <h3 class="mb-0">Your Profile</h3>
                    </div>
                    <div class="card-body">
                        <div v-if="loading" class="text-center">
                            <div class="spinner-border" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                        </div>
                        <div v-if="error" class="alert alert-danger">{{ error }}</div>
                        <div v-if="profileData">
                            <div class="mb-3">
                                <label class="form-label fw-bold">Username</label>
                                <p class="form-control-plaintext">{{ profileData.username }}</p>
                            </div>
                            <hr>
                            <div class="mb-3">
                                <label class="form-label fw-bold">Email</label>
                                <p class="form-control-plaintext">{{ profileData.email }}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { apiRequest } from '../services/api.js';

const profileData = ref(null);
const loading = ref(false);
const error = ref(null);

const fetchProfile = async () => {
    loading.value = true;
    error.value = null;
    try {
        profileData.value = await apiRequest('/profile');
    } catch (err) {
        error.value = err.message;
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    fetchProfile();
});
</script>
