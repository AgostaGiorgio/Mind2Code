<script setup>
import { computed, ref, watch } from 'vue'
import { Plus } from '@lucide/vue'
import { createProject } from '@/services/api'
import { useToast } from '@/composables/useToast'
import BottomSheet from '@/components/ui/BottomSheet.vue'
import TextArea from '@/components/ui/TextArea.vue'
import Toggle from '@/components/ui/Toggle.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'created'])

const toast = useToast()

const userInput = ref('')
const auto = ref(false)
const submitting = ref(false)
const error = ref('')

const canSubmit = computed(() => userInput.value.trim().length > 0 && !submitting.value)

function reset() {
  userInput.value = ''
  auto.value = false
  error.value = ''
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) reset()
  },
)

async function submit() {
  if (!canSubmit.value) return

  submitting.value = true
  error.value = ''
  try {
    const project = await createProject({
      userInput: userInput.value.trim(),
      auto: auto.value,
    })
    toast.success('Project created.')
    emit('created', project)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to create the project.'
    toast.error(error.value)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <BottomSheet :open="open" title="New project" @close="emit('close')">
    <form id="create-project-form" class="flex flex-col gap-4" @submit.prevent="submit">
      <TextArea
        v-model="userInput"
        label="User input"
        placeholder="Describe what you want to build…"
        :rows="8"
        :maxlength="100000"
        :disabled="submitting"
        hint="Required. This becomes the brief for the pipeline."
      />

      <Toggle
        v-model="auto"
        label="Auto"
        :disabled="submitting"
        description="Run every step automatically, one after another. Leave it off to advance manually."
      />

      <p v-if="error" class="text-sm text-red-400" role="alert">{{ error }}</p>
    </form>

    <template #footer>
      <button
        type="submit"
        form="create-project-form"
        :disabled="!canSubmit"
        class="inline-flex min-h-[44px] w-full items-center justify-center gap-2 rounded-app bg-brand-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Plus :size="16" />
        {{ submitting ? 'Creating…' : 'Create project' }}
      </button>
    </template>
  </BottomSheet>
</template>
