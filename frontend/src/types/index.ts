export interface Project {
  id: string
  executionId: number
  name: string
  githubUrl: string
  completionPercentage: number
  finalizationPercentage: number
  auto: boolean
  finalRepoUrl: string | null
  finalizeError: string | null
  createdAt: string
  updatedAt: string
}

export interface ProjectDetail extends Project {
  userInput: string | null
  requirements: string | null
  codeSummary: string | null
  testSummary: string | null
  finalReview: string | null
  retrospective: string | null
}

export interface ProgressEvent {
  executionId: number
  completionPercentage: number
}

export interface FinalizationEvent {
  executionId: number
  finalizationPercentage: number
  finalRepoUrl: string | null
  finalizeError: string | null
}

export interface ProgressUpdatePayload {
  completionPercentage: number
}

export interface CreateProjectPayload {
  userInput: string
  auto: boolean
}

export interface ApiError {
  status: number
  message: string
}
