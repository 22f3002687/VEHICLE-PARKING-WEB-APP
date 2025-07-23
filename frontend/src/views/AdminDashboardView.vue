/*Purpose: Main view for all admin functionalities*/


<template>
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Admin Dashboard</h1>
        <button class="btn btn-primary" @click="openLotModal()"><i class="bi bi-plus-circle"></i> Create New Lot</button>
    </div>

    <!-- Message Area -->
    <div v-if="message" class="alert" :class="messageType === 'success' ? 'alert-success' : 'alert-danger'">
        {{ message }}
    </div>

    <!-- Tabs -->
    <ul class="nav nav-tabs mb-3">
        <li class="nav-item">
            <a class="nav-link" :class="{ active: currentTab === 'lots' }" @click="currentTab = 'lots'">Parking Lots</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" :class="{ active: currentTab === 'users' }" @click="fetchUsers">Users</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" :class="{ active: currentTab === 'reservations' }" @click="fetchReservations">Reservations</a>
        </li>
    </ul>

    <!-- Lots View -->
    <div v-if="currentTab === 'lots'">
        <div v-if="loading" class="text-center p-5"><div class="spinner-border"></div></div>
        <div v-else-if="lots.length === 0" class="text-center p-5 bg-light rounded">
            <p>No parking lots found. Click 'Create New Lot' to get started.</p>
        </div>
        <div v-else class="row">
            <div v-for="lot in lots" :key="lot.id" class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100 shadow-sm">
                    <div class="card-body">
                        <h5 class="card-title">{{ lot.location_name }}</h5>
                        <h6 class="card-subtitle mb-2 text-muted">{{ lot.address }}, {{ lot.pincode }}</h6>
                        <p class="card-text">
                            <strong>Price:</strong> ₹{{ lot.price_per_hour.toFixed(2) }} / hour <br>
                            <strong>Capacity:</strong> {{ lot.available_spots }} / {{ lot.total_spots }} available
                        </p>
                    </div>
                    <div class="card-footer bg-white border-0">
                        <button class="btn btn-sm btn-info me-2" @click="viewLotDetails(lot.id)">Details</button>
                        <button class="btn btn-sm btn-warning me-2" @click="openLotModal(lot)">Edit</button>
                        <button class="btn btn-sm btn-danger" @click="handleDeleteLot(lot.id)">Delete</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Users View -->
    <div v-if="currentTab === 'users'">
        <div v-if="loading" class="text-center p-5"><div class="spinner-border"></div></div>
        <div v-else-if="users.length === 0" class="text-center p-5 bg-light rounded"><p>No registered users found.</p></div>
        <div v-else class="card shadow-sm"><div class="card-body">
            <h3 class="card-title">Registered Users</h3>
            <table class="table table-striped">
                <thead><tr><th>ID</th><th>Username</th><th>Email</th></tr></thead>
                <tbody><tr v-for="user in users" :key="user.id">
                    <td>{{ user.id }}</td><td>{{ user.username }}</td><td>{{ user.email }}</td>
                </tr></tbody>
            </table>
        </div></div>
    </div>
    <!-- Reservations View -->
    <div v-if="currentTab === 'reservations'">
        <h3>All Parking Records</h3>
        <div v-if="loading" class="text-center p-5"><div class="spinner-border"></div></div>
        <div v-else-if="reservations.length === 0" class="text-center p-4 bg-light rounded"><p>No reservations found in the system.</p></div>
        <div v-else class="table-responsive">
            <table class="table table-striped table-hover align-middle">
                <thead class="table-dark">
                    <tr>
                        <th>User</th>
                        <th>Lot Name</th>
                        <th>Spot #</th>
                        <th>Status</th>
                        <th>Booked On</th>
                        <th>Parked On</th>
                        <th>Left On</th>
                        <th>Cost</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="r in reservations" :key="r.id">
                        <td>{{ r.user_name || 'Unknown User' }}</td>
                        <td>{{ r.lot?.location_name || 'Unknown Lot' }}</td>
                        <td>{{ r.spot?.spot_number || 'N/A' }}</td>
                        <td>
                            <span v-if="!r.is_active && r.parking_timestamp" class="badge bg-secondary">Completed</span>
                            <span v-else-if="!r.is_active && !r.parking_timestamp" class="badge bg-danger">Cancelled</span>
                            <span v-else-if="r.is_active && r.parking_timestamp" class="badge bg-success">Parked</span>
                            <span v-else-if="r.is_active && !r.parking_timestamp" class="badge bg-warning text-dark">Booked</span>
                        </td>
                        <td>{{ new Date(r.booking_timestamp).toLocaleString() }}</td>
                        <td>{{ r.parking_timestamp ? new Date(r.parking_timestamp).toLocaleString() : 'N/A' }}</td>
                        <td>{{ r.leaving_timestamp ? new Date(r.leaving_timestamp).toLocaleString() : 'N/A' }}</td>
                        <td>₹{{ r.parking_cost != null ? r.parking_cost.toFixed(2) : '0.00' }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Modals -->
    <LotModal v-if="showModal" :lot-data="selectedLot" @close="showModal = false" @save="handleSaveLot" />
    <LotDetailsModal v-if="showDetailsModal" :lot-details="selectedLotDetails" @close="showDetailsModal = false" />

</template>

<script setup>
import { ref, onMounted } from 'vue';
import { apiRequest } from '../services/api.js';
import LotModal from '../components/LotModal.vue';
import LotDetailsModal from '../components/LotDetailsModal.vue';

const lots = ref([]);
const users = ref([]);
const reservations = ref([]);
const loading = ref(false);
const currentTab = ref('lots');
const message = ref('');
const messageType = ref('');

// Modal state
const showModal = ref(false);
const selectedLot = ref(null);
const showDetailsModal = ref(false);
const selectedLotDetails = ref(null);

const showMessage = (msg, type = 'error', duration = 4000) => {
    message.value = msg;
    messageType.value = type;
    setTimeout(() => message.value = '', duration);
};

const fetchLots = async () => {
    loading.value = true;
    try {
        lots.value = await apiRequest('/admin/lots');
    } catch (err) {
        showMessage(err.message, 'error');
    } finally {
        loading.value = false;
    }
};

const fetchUsers = async () => {
    currentTab.value = 'users';
    loading.value = true;
    try {
        users.value = await apiRequest('/admin/users');
    } catch (err) {
        showMessage(err.message, 'error');
    } finally {
        loading.value = false;
    }
};

const fetchReservations = async () => {
    currentTab.value = 'reservations';
    loading.value = true;
    try {
        reservations.value = await apiRequest('/admin/reservations');
    } catch (err) {
        showMessage(err.message, 'error');
    } finally {
        loading.value = false;
    }
};

const openLotModal = (lot = null) => {
    selectedLot.value = lot;
    showModal.value = true;
};

const handleSaveLot = async (lotData) => {
    const isCreating = !lotData.id;
    const endpoint = isCreating ? '/admin/lots' : `/admin/lots/${lotData.id}`;
    const method = isCreating ? 'POST' : 'PUT';

    try {
        const result = await apiRequest(endpoint, method, lotData);
        showMessage(result.msg, 'success');
        showModal.value = false;
        fetchLots();
    } catch (err) {
        showMessage(err.message, 'error');
    }
};

const handleDeleteLot = async (lotId) => {
    if (confirm('Are you sure you want to delete this parking lot? This cannot be undone.')) {
        try {
            const result = await apiRequest(`/admin/lots/${lotId}`, 'DELETE');
            showMessage(result.msg, 'success');
            fetchLots();
        } catch (err) {
            showMessage(err.message, 'error');
        }
    }
};

const viewLotDetails = async (lotId) => {
    try {
        selectedLotDetails.value = await apiRequest(`/admin/lots/${lotId}`);
        showDetailsModal.value = true;
    } catch (err) {
        showMessage(err.message, 'error');
    }
};

onMounted(fetchLots);
</script>
