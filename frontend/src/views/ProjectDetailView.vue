<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Check, Pencil, RefreshCw, TriangleAlert, X } from '@lucide/vue'
import { getProject, retryProjectPhase, updateProjectName } from '@/services/api'
import { renderMarkdown } from '@/utils/markdown'
import { useSse } from '@/composables/useSse'
import { useToast } from '@/composables/useToast'
import Badge from '@/components/ui/Badge.vue'
import DualProgressRing from '@/components/ui/DualProgressRing.vue'
import GitHubLink from '@/components/ui/GitHubLink.vue'
import PhaseStepper from '@/components/ui/PhaseStepper.vue'
import Skeleton from '@/components/ui/Skeleton.vue'

const route = useRoute()
const projectId = String(route.params.projectId ?? '')
const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

const toast = useToast()

// The pipeline, in the order the phases are produced by the external service.
const PHASES = [
  { value: 'userInput', label: 'User Input', short: 'Input' },
  {
    value: 'requirements',
    label: 'Requirements',
    short: 'Reqs',
    runningStatus: 'REQUIREMENTS_RUNNING',
    doneRank: 2,
  },
  {
    value: 'codeSummary',
    label: 'Code',
    short: 'Code',
    runningStatus: 'CODE_RUNNING',
    doneRank: 4,
  },
  {
    value: 'testSummary',
    label: 'Tests',
    short: 'Tests',
    runningStatus: 'TEST_RUNNING',
    doneRank: 6,
  },
  {
    value: 'finalReview',
    label: 'Review',
    short: 'Review',
    runningStatus: 'REVIEW_RUNNING',
    doneRank: 8,
  },
  {
    value: 'retrospective',
    label: 'Retrospective',
    short: 'Retro',
    runningStatus: 'RETROSPECTIVE_RUNNING',
    doneRank: 10,
  },
]

// Rank of each reported status; ERROR has no position on the line.
const STATUS_RANK = {
  REQUIREMENTS_RUNNING: 1,
  REQUIREMENTS_DONE: 2,
  CODE_RUNNING: 3,
  CODE_DONE: 4,
  TEST_RUNNING: 5,
  TEST_DONE: 6,
  REVIEW_RUNNING: 7,
  REVIEW_DONE: 8,
  RETROSPECTIVE_RUNNING: 9,
  RETROSPECTIVE_DONE: 10,
}

const project = ref(null)
const activePhase = ref(null)
// While true, the newest available phase stays selected (initial default and
// live progress). A manual pick on an earlier phase disables it.
const followLatest = ref(true)
const loading = ref(true)
const error = ref(null)

const editing = ref(false)
const draftName = ref('')
const saving = ref(false)

function hasContent(value) {
  return typeof value === 'string' && value.trim().length > 0
}

const statusRank = computed(() =>
  project.value?.status ? (STATUS_RANK[project.value.status] ?? 0) : 0,
)

// ERROR does not say which phase failed: mark the first phase without content,
// falling back to the last phase when every document is already there.
const errorPhase = computed(() => {
  if (project.value?.status !== 'ERROR') return null
  const pending = PHASES.find(
    (phase) => phase.value !== 'userInput' && !hasContent(project.value?.[phase.value]),
  )
  return (pending ?? PHASES[PHASES.length - 1]).value
})

const phaseOptions = computed(() =>
  PHASES.map((phase) => {
    const hasDoc = hasContent(project.value?.[phase.value])
    const done =
      phase.value === 'userInput'
        ? hasDoc || statusRank.value > 0
        : hasDoc || (phase.doneRank ? statusRank.value >= phase.doneRank : false)
    return {
      ...phase,
      available: hasDoc,
      done,
      running: phase.runningStatus
        ? project.value?.status === phase.runningStatus
        : false,
      error: errorPhase.value === phase.value,
    }
  }),
)

const RETRY_PHASES = {
  requirements: { label: 'Requirements', value: 'REQUIREMENTS' },
  codeSummary: { label: 'Code', value: 'CODE' },
  testSummary: { label: 'Tests', value: 'TEST' },
  finalReview: { label: 'Review', value: 'REVIEW' },
  retrospective: { label: 'Retrospective', value: 'RETROSPECTIVE' },
}

const failedPhase = computed(() =>
  errorPhase.value ? (RETRY_PHASES[errorPhase.value] ?? null) : null,
)

const retrying = ref(false)
const retryError = ref('')

const lastAvailablePhase = computed(() => {
  for (let i = PHASES.length - 1; i >= 0; i -= 1) {
    if (hasContent(project.value?.[PHASES[i].value])) return PHASES[i].value
  }
  return null
})

const activeContent = computed(() =>
  project.value && activePhase.value ? project.value[activePhase.value] : null,
)
const renderedContent = computed(() => renderMarkdown(activeContent.value))

// The finalization arc only matters once the release has started or finished.
const showFinalization = computed(
  () => Boolean(project.value?.finalRepoUrl) || (project.value?.finalizationPercentage ?? 0) > 0,
)

// Select the latest phase with content, unless the user picked another one.
function syncActivePhase() {
  const latest = lastAvailablePhase.value
  const activeMissing = !activePhase.value || !hasContent(project.value?.[activePhase.value])

  if (followLatest.value || activeMissing) {
    activePhase.value = latest
  }
}

function selectPhase(value) {
  followLatest.value = value === lastAvailablePhase.value
  activePhase.value = value
}

async function load() {
  if (!UUID_PATTERN.test(projectId)) {
    error.value = 'Invalid project id.'
    loading.value = false
    return
  }

  loading.value = true
  error.value = null
  try {
    project.value = await getProject(projectId)
    syncActivePhase()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load the project.'
  } finally {
    loading.value = false
  }
}

async function refresh() {
  try {
    project.value = await getProject(projectId)
    syncActivePhase()
  } catch {
    // Keep the previously loaded project if the refresh fails.
  }
}

async function retryFailedPhase() {
  const phase = failedPhase.value
  if (!phase || retrying.value) return

  retrying.value = true
  retryError.value = ''
  try {
    project.value = await retryProjectPhase(projectId, phase.value)
    syncActivePhase()
    toast.success(`${phase.label} phase restarted.`)
  } catch (e) {
    retryError.value = e instanceof Error ? e.message : 'Could not retry the phase.'
    toast.error(retryError.value)
    await refresh()
  } finally {
    retrying.value = false
  }
}

function startEdit() {
  draftName.value = project.value.name
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  draftName.value = ''
}

async function saveName() {
  const name = draftName.value.trim()
  if (!name || saving.value) return

  saving.value = true
  try {
    project.value = await updateProjectName(projectId, name)
    editing.value = false
    draftName.value = ''
    toast.success('Project renamed.')
  } catch (e) {
    toast.error(e instanceof Error ? e.message : 'Failed to rename the project.')
  } finally {
    saving.value = false
  }
}

// Keep the header percentage live and refresh the documents on progress events.
useSse(
  (event) => {
    if (!project.value || event.projectId !== projectId) return
    project.value.completionPercentage = event.completionPercentage
    project.value.status = event.status
    refresh()
  },
  (event) => {
    if (!project.value || event.projectId !== projectId) return
    project.value.finalizationPercentage = event.finalizationPercentage
    project.value.finalRepoUrl = event.finalRepoUrl
    project.value.finalizeError = event.finalizeError
    // Once finalized, re-fetch so the retrospective (written by n8n) shows up.
    if (event.finalRepoUrl) refresh()
  },
)

onMounted(load)
</script>

<template>
  <main class="w-full px-4">
    <div class="mx-auto flex w-full max-w-4xl flex-col gap-5 py-4">
      <RouterLink
        to="/"
        class="inline-flex w-fit min-h-[44px] items-center gap-2 text-sm font-semibold text-brand-textMuted transition-colors hover:text-brand-textMain"
      >
        <ArrowLeft :size="18" />
        Back to projects
      </RouterLink>

      <!-- Loading state -->
      <div v-if="loading" class="app-card rounded-app p-5">
        <Skeleton :lines="3" />
      </div>

      <!-- Error state -->
      <div
        v-else-if="error"
        class="app-card rounded-app flex flex-col items-center gap-4 p-6 text-center"
        role="alert"
      >
        <p class="font-semibold text-brand-textMain">Unable to load project</p>
        <p class="text-sm text-brand-textMuted">{{ error }}</p>
        <button
          type="button"
          class="inline-flex min-h-[44px] items-center gap-2 rounded-app bg-brand-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-primary/90"
          @click="load"
        >
          <RefreshCw :size="16" />
          Retry
        </button>
      </div>

      <template v-else-if="project">
        <!-- Header: repository icons, editable title, completion + finalization rings -->
        <div class="app-card rounded-app flex min-w-0 items-center gap-4 p-5">
          <div class="flex shrink-0 flex-row items-center gap-2">
            <GitHubLink
              :url="project.githubUrl"
              :label="`Open the demo repository for ${project.name}`"
            />
            <GitHubLink
              v-if="project.finalRepoUrl"
              :url="project.finalRepoUrl"
              :label="`Open the finalized repository for ${project.name}`"
            />
          </div>

          <div class="min-w-0 flex-1">
            <div v-if="!editing" class="flex min-w-0 items-center gap-2">
              <h1
                class="min-w-0 break-words text-lg font-extrabold leading-tight text-brand-textMain sm:text-xl"
              >
                {{ project.name }}
              </h1>
              <Badge v-if="project.auto" color="#34d399" dot class="shrink-0">Auto</Badge>
              <button
                type="button"
                class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-brand-textMuted transition-colors hover:bg-brand-surface/60 hover:text-brand-textMain"
                :aria-label="`Rename project ${project.name}`"
                @click="startEdit"
              >
                <Pencil :size="15" />
              </button>
            </div>

            <form
              v-else
              class="flex min-w-0 flex-col gap-2 sm:flex-row sm:items-center"
              @submit.prevent="saveName"
            >
              <input
                v-model="draftName"
                type="text"
                maxlength="200"
                aria-label="Project name"
                class="min-w-0 flex-1 rounded-app-sm border border-white/10 bg-brand-surface/60 px-3 py-2 text-sm text-brand-textMain focus:border-brand-primary focus:outline-none"
              />
              <div class="flex shrink-0 items-center gap-2">
                <button
                  type="submit"
                  class="inline-flex h-9 items-center gap-1.5 rounded-app bg-brand-primary px-3 text-xs font-semibold text-white transition-colors hover:bg-brand-primary/90 disabled:opacity-60"
                  :disabled="saving"
                >
                  <Check :size="14" />
                  Save
                </button>
                <button
                  type="button"
                  class="inline-flex h-9 items-center gap-1.5 rounded-app border border-white/10 bg-brand-surface/60 px-3 text-xs font-semibold text-brand-textMuted transition-colors hover:text-brand-textMain disabled:opacity-60"
                  :disabled="saving"
                  @click="cancelEdit"
                >
                  <X :size="14" />
                  Cancel
                </button>
              </div>
            </form>
          </div>

          <span class="inline-flex shrink-0" aria-live="polite" aria-atomic="true">
            <DualProgressRing
              :primary-value="project.completionPercentage"
              :secondary-value="showFinalization ? project.finalizationPercentage : null"
            />
          </span>
        </div>

        <!-- Pipeline phases + selected document -->
        <div class="app-card rounded-app flex min-w-0 flex-col gap-5 p-5">
          <div
            v-if="project.status === 'ERROR' && failedPhase"
            class="flex flex-col gap-3 rounded-app-sm border border-red-400/30 bg-red-500/10 p-3 sm:flex-row sm:items-center"
            role="alert"
          >
            <div class="flex min-w-0 flex-1 items-start gap-2">
              <TriangleAlert :size="16" class="mt-0.5 shrink-0 text-red-400" />
              <div class="min-w-0">
                <p class="text-sm font-semibold text-brand-textMain">
                  Pipeline error on {{ failedPhase.label }}
                </p>
                <p v-if="retryError" class="text-xs text-red-400">{{ retryError }}</p>
                <p v-else class="text-xs text-brand-textMuted">
                  Retry this phase to continue the pipeline.
                </p>
              </div>
            </div>

            <button
              type="button"
              class="inline-flex min-h-[40px] shrink-0 items-center justify-center gap-2 rounded-app bg-red-500 px-3 text-xs font-semibold text-white transition-colors hover:bg-red-400 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="retrying"
              @click="retryFailedPhase"
            >
              <RefreshCw :size="14" :class="retrying ? 'animate-spin' : ''" />
              {{ retrying ? 'Retrying…' : 'Retry' }}
            </button>
          </div>

          <PhaseStepper
            :model-value="activePhase"
            :options="phaseOptions"
            @update:model-value="selectPhase"
          />

          <div
            v-if="activeContent"
            class="markdown-body min-w-0 max-w-full break-words border-t border-white/5 pt-4"
            v-html="renderedContent"
          ></div>

          <p v-else class="py-8 text-center text-sm text-brand-textMuted">
            No documents yet. They will appear here as the pipeline progresses.
          </p>
        </div>
      </template>
    </div>
  </main>
</template>
