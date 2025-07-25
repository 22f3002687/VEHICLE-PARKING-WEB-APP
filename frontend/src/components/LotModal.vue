<template>
    <div class="modal-backdrop fade show"></div>
    <div class="modal fade show" style="display: block;" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">{{ isEditing ? 'Edit' : 'Create' }} Parking Lot</h5>
                    <button type="button" class="btn-close" @click="$emit('close')"></button>
                </div>
                <div class="modal-body">
                    <form @submit.prevent="save">
                        <div class="mb-3"><label>Location Name</label><input v-model="form.location_name" class="form-control" required></div>
                        <div class="mb-3"><label>Address</label><input v-model="form.address" class="form-control" required></div>
                        <div class="mb-3"><label>Pincode</label><input v-model="form.pincode" class="form-control" required></div>
                        <div class="mb-3"><label>Total Spots</label><input v-model.number="form.total_spots" type="number" min="1" class="form-control" required></div>
                        <div class="mb-3"><label>Price per Hour (₹)</label><input v-model.number="form.price_per_hour" type="number" step="0.01" min="0.01" class="form-control" required></div>
                        <div class="modal-footer border-0 px-0">
                            <button type="button" class="btn btn-secondary" @click="$emit('close')">Close</button>
                            <button type="submit" class="btn btn-primary">Save Changes</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
    lotData: {
        type: Object,
        default: null
    }
});
const emit = defineEmits(['close', 'save']);

const isEditing = computed(() => !!props.lotData);

const form = ref({
    id: props.lotData?.id || null,
    location_name: props.lotData?.location_name || '',
    address: props.lotData?.address || '',
    pincode: props.lotData?.pincode || '',
    total_spots: props.lotData?.total_spots || 10,
    price_per_hour: props.lotData?.price_per_hour || 50.00
});

const save = () => {
    emit('save', form.value);
};
</script>