import { computed, reactive, readonly, type DeepReadonly } from 'vue'
import { getProjects } from '@/services/api'
import type { FinalizationEvent, ProgressEvent, Project } from '@/types'

interface ProjectsState {
  projects: Record<number, Project>
  loading: boolean
  error: string | null
}

const state = reactive<ProjectsState>({
  projects: {},
  loading: false,
  error: null,
})

function indexProjects(projects: Project[]): Record<number, Project> {
  return projects.reduce((acc, project) => {
    acc[project.executionId] = project
    return acc
  }, {} as Record<number, Project>)
}

export function useProjectsStore() {
  const load = async () => {
    state.loading = true
    state.error = null
    try {
      const projects = await getProjects()
      state.projects = indexProjects(projects)
    } catch (error) {
      state.error = error instanceof Error ? error.message : 'Failed to load projects.'
    } finally {
      state.loading = false
    }
  }

  const applyProgressEvent = (event: ProgressEvent) => {
    const project = state.projects[event.executionId]
    if (project) {
      project.completionPercentage = event.completionPercentage
    }
  }

  const applyFinalizationEvent = (event: FinalizationEvent) => {
    const project = state.projects[event.executionId]
    if (project) {
      project.finalizationPercentage = event.finalizationPercentage
      project.finalRepoUrl = event.finalRepoUrl
      project.finalizeError = event.finalizeError
    }
  }

  const list = computed(() =>
    Object.values(state.projects).sort(
      (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
    ),
  )

  const hasProjects = computed(() => list.value.length > 0)

  return {
    state: readonly(state) as DeepReadonly<ProjectsState>,
    list,
    hasProjects,
    load,
    retry: load,
    applyProgressEvent,
    applyFinalizationEvent,
  }
}
