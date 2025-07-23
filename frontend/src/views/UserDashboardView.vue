/*Purpose: The main dashboard for regular users*/


<template>
    <div class="container my-4">
        <div v-if="message" class="alert alert-dismissible fade show" :class="messageType === 'success' ? 'alert-success' : 'alert-danger'">
            {{ message }}
            <button type="button" class="btn-close" @click="message = ''"></button>
        </div>

        <!-- Active Reservations -->
        <div v-if="activeReservations.length > 0">
            <h3>Your Active Bookings</h3>
            <div class="list-group">
                <div v-for="r in activeReservations" :key="r.id" class="list-group-item list-group-item-action flex-column align-items-start">
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">Lot: {{ r.lot.location_name }}</h5>
                        <small>Spot #{{ r.spot.spot_number }}</small>
                    </div>
                    <p class="mb-1">Booked at: {{ new Date(r.booking_timestamp).toLocaleString() }}</p>
                    <p v-if="r.parking_timestamp" class="mb-1">Parked since: {{ new Date(r.parking_timestamp).toLocaleString() }}</p>
                    <div class="mt-2">
                        <div v-if="!r.parking_timestamp">
                            <button @click="park(r.id)" class="btn btn-sm btn-success me-2">Park Vehicle</button>
                            <button @click="vacate(r.id)" class="btn btn-sm btn-danger">Cancel Booking</button>
                        </div>
                        <button v-else @click="vacate(r.id)" class="btn btn-sm btn-warning">Vacate Spot</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Available Lots -->
         
        <div>
            <h3>Available Parking Lots</h3>
            <div v-if="loading" class="text-center p-5"><div class="spinner-border"></div></div>
            <div v-else-if="lots.length === 0" class="text-center p-4 bg-light rounded"><p>No parking lots available.</p></div>
            <div v-else class="row">
                <div v-for="lot in lots" :key="lot.id" class="col-md-6 col-lg-4 mb-4">
                    <div class="card h-100 shadow-sm">
                        <div class="card-body d-flex flex-column">
                            <h5 class="card-title">{{ lot.location_name }}</h5>
                            <h6 class="card-subtitle mb-2 text-muted">{{ lot.address }}</h6>
                            <p class="card-text mt-auto">
                                <strong>Price:</strong> ₹{{ lot.price_per_hour.toFixed(2) }} / hour <br>
                                <strong>Availability:</strong> {{ lot.available_spots }} / {{ lot.total_spots }} spots
                            </p>
                            <button @click="openBookingModal(lot)" class="btn btn-primary mt-3" :disabled="lot.available_spots === 0">
                                {{ lot.available_spots > 0 ? 'Book Spots' : 'Lot Full' }}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <hr class="my-4">

        <!-- Parking History -->
        <h3>Your Parking History</h3>
        <div v-if="loading" class="text-center p-5"><div class="spinner-border"></div></div>
        <div v-else-if="pastReservations.length === 0" class="text-center p-4 bg-light rounded"><p>You have no past parking records.</p></div>
        <div v-else class="table-responsive">
            <table class="table table-striped table-hover align-middle">
                <thead class="table-dark">
                    <tr><th>Lot Name</th><th>Spot #</th><th>Booked On</th><th>Parked On</th><th>Left On</th><th>Duration</th><th>Cost</th></tr>
                </thead>
                <tbody>
                    <tr v-for="r in pastReservations" :key="r.id">
                        <td>{{ r.lot.location_name }}</td>
                        <td>{{ r.spot.spot_number }}</td>
                        <td>{{ new Date(r.booking_timestamp).toLocaleString() }}</td> 
                        <td>{{ r.parking_timestamp ? new Date(r.parking_timestamp).toLocaleString() : 'N/A' }}</td>
                        <td>{{ r.leaving_timestamp ? new Date(r.leaving_timestamp).toLocaleString() : 'N/A' }}</td>
                        <td>{{ formatDuration(r.parking_timestamp, r.leaving_timestamp) }}</td>
                        <td>₹{{ r.parking_cost != null ? r.parking_cost.toFixed(2) : '0.00' }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <!-- Booking Modal -->
    <BookingModal v-if="showBookingModal" :lot="selectedLot" @close="showBookingModal = false" @book="handleBooking" />
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { apiRequest } from '../services/api.js';
import BookingModal from '../components/BookingModal.vue';

const lots = ref([]);
const reservations = ref([]);
const message = ref('');
const messageType = ref('');
const loading = ref(false);
const showBookingModal = ref(false);
const selectedLot = ref(null);

const activeReservations = computed(() => reservations.value.filter(r => r.is_active));
const pastReservations = computed(() => reservations.value.filter(r => !r.is_active));

const formatDuration = (start, end) => {
    if (!start || !end) {
        return 'N/A';
    }
    const startDate = new Date(start);
    const endDate = new Date(end);
    const diffMs = endDate - startDate;
    if (diffMs < 0) return 'N/A';

    const hours = Math.floor(diffMs / 3600000);
    const minutes = Math.floor((diffMs % 3600000) / 60000);
    
    return `${hours}h ${minutes}m`;
};


const showMessage = (msg, type = 'error') => {
    message.value = msg;
    messageType.value = type;
};

const fetchData = async () => {
    loading.value = true;
    try {
        const [lotsData, reservationsData] = await Promise.all([
            apiRequest('/user/lots'),
            apiRequest('/user/reservations')
        ]);
        lots.value = lotsData;
        reservations.value = reservationsData;
    } catch (err) {
        showMessage(err.message, 'error');
    } finally {
        loading.value = false;
    }
};

const openBookingModal = (lot) => {
    selectedLot.value = lot;
    showBookingModal.value = true;
};

const handleBooking = async ({ lotId, numSpots }) => {
    showBookingModal.value = false;
    try {
        const data = await apiRequest('/user/reservations/book', 'POST', { lot_id: lotId, number_of_spots: numSpots });
        showMessage(data.msg, 'success');
        fetchData();
    } catch (err) {
        showMessage(err.message, 'error');
    }
};

const park = async (reservationId) => {
    try {
        const data = await apiRequest('/user/reservations/park', 'PUT', { reservation_id: reservationId });
        showMessage(data.msg, 'success');
        fetchData();
    } catch (err) {
        showMessage(err.message, 'error');
    }
};

const vacate = async (reservationId) => {
    try {
        const data = await apiRequest('/user/reservations/vacate', 'PUT', { reservation_id: reservationId });
        showMessage(`${data.msg}`, 'success');
        fetchData();
    } catch (err) {
        showMessage(err.message, 'error');
    }
};

onMounted(fetchData);
</script>

