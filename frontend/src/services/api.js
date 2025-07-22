  /* Purpose: Centralized service for API communication and auth state. */

  import { ref } from 'vue';

const API_URL = 'http://127.0.0.1:5000/api';

// Reactive object to hold authentication state
export const auth = ref({
    token: localStorage.getItem('token') || null,
    role: localStorage.getItem('role') || null,
    username: localStorage.getItem('username') || null,
});

// Central API request function
export async function apiRequest(endpoint, method = 'GET', data = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (auth.value.token) {
        headers['Authorization'] = `Bearer ${auth.value.token}`;
    }

    const config = { method, headers };
    if (data) {
        config.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(API_URL + endpoint, config);
        const responseData = await response.json();

        if (response.status === 401) {
            logout();
            window.location.href = '/login';
            throw new Error("Session expired. Please log in again.");
        }
        if (!response.ok) {
            throw new Error(responseData.msg || 'An API error occurred');
        }
        return responseData;
    } catch (error) {
        console.error("API Request Error:", error);
        throw error;
    }
}

// Auth helper functions
export function login(token, role, username) {
    auth.value = { token, role, username };
    localStorage.setItem('token', token);
    localStorage.setItem('role', role);
    localStorage.setItem('username', username);
}

export function logout() {
    auth.value = { token: null, role: null, username: null };
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('username');
}