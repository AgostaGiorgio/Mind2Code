<script setup>
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, RefreshCw } from '@lucide/vue'
import { useProjectCreation } from '@/composables/useProjectCreation'
import Skeleton from '@/components/ui/Skeleton.vue'

const router = useRouter()
const creation = useProjectCreation()
const { state } = creation

watch(
  () => state.status,
  async (status) => {
    if (status === 'created' && state.project) {
      const { id } = state.project
      await router.replace(`/projects/${id}`)
      creation.reset()
    }
  },
  { immediate: true },
)

onMounted(() => {
  // Direct visit / page reload without an in-flight creation.
  if (state.status === 'idle') {
    router.replace('/')
  }
})

function retry() {
  creation.retry()
}

function goBack() {
  creation.reset()
  router.push('/')
}
</script>

<template>
  <main class="w-full px-4">
    <div class="mx-auto flex w-full max-w-4xl flex-col gap-5 py-4">
      <RouterLink
        to="/"
        class="inline-flex w-fit min-h-[44px] items-center gap-2 text-sm font-semibold text-brand-textMuted transition-colors hover:text-brand-textMain"
        @click="creation.reset()"
      >
        <ArrowLeft :size="18" />
        Back to projects
      </RouterLink>

      <!-- Error state -->
      <div
        v-if="state.status === 'error'"
        class="app-card rounded-app flex flex-col items-center gap-4 p-6 text-center"
        role="alert"
      >
        <p class="font-semibold text-brand-textMain">Unable to create project</p>
        <p class="text-sm text-brand-textMuted">{{ state.error }}</p>
        <div class="flex flex-wrap items-center justify-center gap-2">
          <button
            type="button"
            class="inline-flex min-h-[44px] items-center gap-2 rounded-app bg-brand-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-primary/90"
            @click="retry"
          >
            <RefreshCw :size="16" />
            Retry
          </button>
          <button
            type="button"
            class="inline-flex min-h-[44px] items-center gap-2 rounded-app border border-white/10 bg-brand-surface/60 px-4 py-2.5 text-sm font-semibold text-brand-textMuted transition-colors hover:text-brand-textMain"
            @click="goBack"
          >
            Back to projects
          </button>
        </div>
      </div>

      <!-- Detail-page skeleton while n8n extracts the title and the row is created -->
      <template v-else>
        <p class="text-center text-sm text-brand-textMuted" role="status">
          Creating your project… this can take up to a minute or so.
        </p>

        <div class="app-card rounded-app flex items-center gap-4 p-5">
          <div class="flex shrink-0 items-center gap-2">
            <span class="h-10 w-10 animate-pulse rounded-full bg-white/5" />
            <span class="h-10 w-10 animate-pulse rounded-full bg-white/5" />
          </div>

          <div class="min-w-0 flex-1">
            <span class="block h-5 w-2/3 animate-pulse rounded-app-sm bg-white/5" />
          </div>

          <span class="h-[52px] w-[52px] shrink-0 animate-pulse rounded-full bg-white/5" />
        </div>

        <div class="app-card rounded-app flex min-w-0 flex-col gap-5 p-5">
          <div class="flex items-start justify-between gap-2">
            <div
              v-for="n in 6"
              :key="n"
              class="flex flex-1 flex-col items-center gap-2"
            >
              <span class="h-3 w-3 animate-pulse rounded-full bg-white/5" />
              <span class="h-2 w-10 animate-pulse rounded-full bg-white/5" />
            </div>
          </div>

          <div class="border-t border-white/5 pt-4">
            <Skeleton :lines="6" height="h-4" />
          </div>
        </div>
      </template>
    </div>
  </main>
</template>
