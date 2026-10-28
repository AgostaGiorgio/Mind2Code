<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronRight, FolderOpen, Plus, RefreshCw } from '@lucide/vue'
import { useProjectsStore } from '@/stores/projects'
import { useProjectCreation } from '@/composables/useProjectCreation'
import { isSafeGitHubUrl } from '@/utils/github'
import GitHubLink from '@/components/ui/GitHubLink.vue'
import ProgressRing from '@/components/ui/ProgressRing.vue'
import RetrospectiveControl from '@/components/ui/RetrospectiveControl.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import Skeleton from '@/components/ui/Skeleton.vue'
import CreateProjectSheet from '@/components/CreateProjectSheet.vue'

const store = useProjectsStore()
const { state, list, hasProjects } = store

const router = useRouter()
const createOpen = ref(false)
const projectCreation = useProjectCreation()

function goToDetail(projectId) {
  router.push(`/projects/${projectId}`)
}

function handleCreate(payload) {
  createOpen.value = false
  projectCreation.start(payload)
  router.push('/projects/new')
}

onMounted(() => {
  store.load()
})
</script>

<template>
  <main class="flex w-full flex-1 flex-col px-4">
    <div class="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-5 py-4">
      <div class="flex items-center justify-between gap-3">
        <h1 class="text-xl font-extrabold tracking-tight text-brand-textMain">
          Projects
        </h1>

        <button
          type="button"
          class="inline-flex min-h-[40px] items-center gap-1.5 rounded-app bg-brand-primary px-3 text-xs font-semibold text-white transition-colors hover:bg-brand-primary/90"
          aria-label="New project"
          @click="createOpen = true"
        >
          <Plus :size="16" />
          <span class="sm:hidden">New</span>
          <span class="hidden sm:inline">New project</span>
        </button>
      </div>

      <!-- Loading state -->
      <div v-if="state.loading" class="flex flex-col gap-5">
        <div v-for="n in 3" :key="n" class="app-card rounded-app p-5 flex flex-col gap-4">
          <Skeleton :lines="1" height="h-5" class="w-1/2" />
          <Skeleton :lines="1" height="h-4" class="w-3/4" />
          <Skeleton :lines="1" height="h-2.5" class="w-full" />
        </div>
      </div>

      <!-- Error state -->
      <div
        v-else-if="state.error"
        class="app-card rounded-app p-6 flex flex-col items-center text-center gap-4"
        role="alert"
      >
        <p class="text-brand-textMain font-semibold">Unable to load projects</p>
        <p class="text-brand-textMuted text-sm">{{ state.error }}</p>
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-app bg-brand-primary px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-primary/90 transition-colors min-h-[44px]"
          @click="store.retry"
        >
          <RefreshCw :size="16" />
          Retry
        </button>
      </div>

      <!-- Empty state -->
      <EmptyState
        v-else-if="!hasProjects"
        :icon="FolderOpen"
        title="No projects yet"
        description="Projects will appear here once they are added to the backend."
      />

      <!-- Project list: a single card holding one row per project -->
      <section
        v-else
        aria-label="Project list"
        class="app-card rounded-app flex flex-1 flex-col p-2 sm:p-3"
      >
        <table class="w-full border-collapse text-left">
          <thead>
            <tr class="text-[11px] uppercase tracking-wide text-brand-textMuted">
              <th scope="col" class="w-full px-2 py-2 font-semibold">Project</th>
              <th scope="col" class="px-2 py-2 text-right font-semibold">Status</th>
              <th scope="col" class="w-12 px-2 py-2">
                <span class="sr-only">Details</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="project in list"
              :key="project.id"
              class="cursor-pointer border-t border-white/5 transition-colors hover:bg-brand-surface/40"
              @click="goToDetail(project.id)"
            >
              <td class="px-2 py-3">
                <div class="flex items-center gap-3">
                  <span
                    v-if="isSafeGitHubUrl(project.finalRepoUrl || project.githubUrl)"
                    class="inline-flex"
                    @click.stop
                  >
                    <GitHubLink
                      :url="project.finalRepoUrl || project.githubUrl"
                      :label="`Open GitHub repository for ${project.name}`"
                    />
                  </span>
                  <span class="min-w-0 break-words text-sm font-semibold text-brand-textMain sm:text-base">
                    {{ project.name }}
                  </span>
                </div>
              </td>

              <td class="px-2 py-3 text-right align-middle">
                <div class="flex items-center justify-end gap-2">
                  <span class="inline-flex" aria-live="polite" aria-atomic="true">
                    <ProgressRing :value="project.completionPercentage" :size="40" />
                  </span>
                  <span class="inline-flex" @click.stop>
                    <RetrospectiveControl :project="project" />
                  </span>
                </div>
              </td>

              <td class="px-2 py-3 text-right">
                <RouterLink
                  :to="`/projects/${project.id}`"
                  class="inline-flex h-10 w-10 items-center justify-center rounded-full text-brand-textMuted transition-colors hover:bg-brand-surface/60 hover:text-brand-textMain"
                  :aria-label="`View details for ${project.name}`"
                  @click.stop
                >
                  <ChevronRight :size="20" />
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>

    <CreateProjectSheet
      :open="createOpen"
      @close="createOpen = false"
      @create="handleCreate"
    />
  </main>
</template>
