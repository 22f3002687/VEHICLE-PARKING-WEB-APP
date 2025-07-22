/*Purpose: A new modal for booking multiple spots*/


<template>
    <div class="modal-backdrop fade show"></div>
    <div class="modal fade show" style="display: block;" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Book Spots at {{ lot.location_name }}</h5>
                    <button type="button" class="btn-close" @click="$emit('close')"></button>
                </div>
                <div class="modal-body">
                    <p>Available Spots: {{ lot.available_spots }}</p>
                    <div class="mb-3">
                        <label for="numSpots" class="form-label">How many spots would you like to book?</label>
                        <input id="numSpots" v-model.number="numberOfSpots" type="number" class="form-control" :max="lot.available_spots" min="1">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" @click="$emit('close')">Cancel</button>
                    <button type="button" class="btn btn-primary" @click="confirmBooking">Confirm Booking</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
    lot: {
        type: Object,
        required: true
    }
});
const emit = defineEmits(['close', 'book']);

const numberOfSpots = ref(1);

const confirmBooking = () => {
    if (numberOfSpots.value > 0 && numberOfSpots.value <= props.lot.available_spots) {
        emit('book', { lotId: props.lot.id, numSpots: numberOfSpots.value });
    } else {
        alert(`Please enter a valid number of spots (1 to ${props.lot.available_spots}).`);
    }
};
</script>