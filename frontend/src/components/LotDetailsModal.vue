<template>
    <div class="modal-backdrop fade show"></div>
    <div class="modal fade show" style="display: block;" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered modal-lg modal-dialog-scrollable">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" v-if="lotDetails">{{ lotDetails.location_name }} - Spot Status</h5>
                    <button type="button" class="btn-close" @click="$emit('close')"></button>
                </div>
                <div class="modal-body">
                    <div v-if="!lotDetails" class="text-center"><div class="spinner-border"></div></div>
                    <div v-else class="d-flex flex-wrap justify-content-center">
                        <div v-for="spot in lotDetails.spots" :key="spot.id" class="spot m-1" :class="spot.status">
                            #{{ spot.spot_number }}
                        </div>
                    </div>
                </div>
                 <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" @click="$emit('close')">Close</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
defineProps({
    lotDetails: {
        type: Object,
        default: null
    }
});
defineEmits(['close']);
</script>

<style scoped>
.spot {
    border-radius: 5px;
    padding: 1rem;
    font-weight: bold;
    color: white;
    width: 80px;
    text-align: center;
}
.spot.Available {
    background-color: #198754; 
}
.spot.Occupied {
    background-color: #dc3545; 
}
.spot.Booked {
    background-color: #ffc107; 
    color: #000;
}
</style>
