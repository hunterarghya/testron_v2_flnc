// Where the student is among the stages (frontend_spec.md §5.3), read from the server's
// clock. The client never moves stages on its own: when the current stage's deadline passes,
// it asks the server again and follows what it says.

export type StageStateName = 'NOT_ENTERED' | 'OPEN' | 'LEFT' | 'CLOSED' | 'MISSED'

export interface StageClock {
  index: number
  state: StageStateName
  deadline_at: string | null
}

export interface ClockView {
  current_stage_index: number
  attempt_deadline: string
  stages: StageClock[]
}

export interface StageMetaView {
  index: number
  question_ids: string[]
}

export function currentStage(clock: ClockView): StageClock | undefined {
  return clock.stages.find(stage => stage.index === clock.current_stage_index)
}

/** The instant the timer counts down to: the current stage's deadline, else the attempt's. */
export function watchedDeadline(clock: ClockView): string {
  return currentStage(clock)?.deadline_at ?? clock.attempt_deadline
}

/** Stages left but still running, which `allow_return` lets the student go back to. */
export function returnableStages(clock: ClockView, allowReturn: boolean): number[] {
  if (!allowReturn) return []
  return clock.stages.filter(stage => stage.state === 'LEFT').map(stage => stage.index)
}

/** On the last stage the button reads "Submit"; before it, "Next section". */
export function isLastStage(clock: ClockView): boolean {
  return clock.current_stage_index >= clock.stages.length - 1
}

/** The palette shows the current stage's questions only. */
export function stageQuestionIds(meta: readonly StageMetaView[], clock: ClockView): string[] {
  return meta.find(stage => stage.index === clock.current_stage_index)?.question_ids ?? []
}
