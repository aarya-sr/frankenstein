export interface BaseMessage {
  type: string
  payload: Record<string, unknown>
  timestamp: string
  session_id: string
}

export interface ChatMessage extends BaseMessage {
  type: "chat.message"
  payload: { text: string }
}

export interface QuestionGroupMessage extends BaseMessage {
  type: "chat.question_group"
  payload: {
    categories: { name: string; confidence: number; questions: string[] }[]
    round: number
    max_rounds: number
  }
}

export interface CheckpointMessage extends BaseMessage {
  type: "chat.checkpoint"
  payload: {
    checkpoint_type: "requirements" | "spec"
    requirements?: Record<string, unknown>
    spec?: Record<string, unknown>
    critique?: Record<string, unknown> | null
    architect_reasoning?: string
  }
}

export interface StageUpdateMessage extends BaseMessage {
  type: "status.stage_update"
  payload: { stage: string; description: string }
}

export interface ProgressMessage extends BaseMessage {
  type: "status.progress"
  payload: { stage: string; percent: number; detail: string }
}

export interface CompleteMessage extends BaseMessage {
  type: "status.complete"
  payload: {
    session_id: string
    framework: string
    download_url: string
    summary: string
  }
}

export interface ErrorMessage extends BaseMessage {
  type: "error.llm_failure" | "error.pipeline_failure"
  payload: { stage: string; message: string; recoverable: boolean }
}

export interface ActivityMessage extends BaseMessage {
  type: "status.activity"
  payload: { agent: string; text: string }
}

export type ServerMessage =
  | ChatMessage
  | QuestionGroupMessage
  | CheckpointMessage
  | StageUpdateMessage
  | ProgressMessage
  | CompleteMessage
  | ErrorMessage
  | ActivityMessage
