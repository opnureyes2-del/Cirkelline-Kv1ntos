/**
 * Google Tasks TypeScript Type Definitions
 *
 * These types match the Google Tasks API v1 response format
 * https://developers.google.com/tasks/reference/rest/v1
 */

export interface TaskList {
  /** Task list identifier */
  id: string

  /** Title of the task list */
  title: string

  /** Last modification time (RFC 3339 timestamp) */
  updated: string

  /** URL pointing to this task list (self link) */
  selfLink?: string

  /** ETag of the resource */
  etag?: string

  /** Type of the resource ("tasks#taskList") */
  kind?: string
}

export interface Task {
  /** Task identifier */
  id: string

  /** Title of the task */
  title: string

  /** Status of the task: "needsAction" or "completed" */
  status: 'needsAction' | 'completed'

  /** Notes describing the task (optional) */
  notes?: string

  /** Due date of the task (RFC 3339 timestamp, optional) */
  due?: string

  /** Completion date (RFC 3339 timestamp, only if status is completed) */
  completed?: string

  /** Parent task identifier (for subtasks) */
  parent?: string

  /** String indicating the position of the task among its sibling tasks under the same parent */
  position?: string

  /** Collection of links (optional) */
  links?: Array<{
    type: string
    description: string
    link: string
  }>

  /** Last modification time (RFC 3339 timestamp) */
  updated: string

  /** Flag indicating whether the task has been deleted (optional) */
  deleted?: boolean

  /** Flag indicating whether the task is hidden (optional) */
  hidden?: boolean

  /** URL pointing to this task (self link) */
  selfLink?: string

  /** ETag of the resource */
  etag?: string

  /** Type of the resource ("tasks#task") */
  kind?: string
}

export interface TasksListResponse {
  /** Type of the resource */
  kind: string

  /** ETag of the collection */
  etag?: string

  /** Token that can be used to retrieve the next page of items */
  nextPageToken?: string

  /** Collection of tasks */
  items: Task[]
}

export interface TaskListsResponse {
  /** Type of the resource */
  kind: string

  /** ETag of the collection */
  etag?: string

  /** Token that can be used to retrieve the next page of items */
  nextPageToken?: string

  /** Collection of task lists */
  items: TaskList[]
}

/**
 * Request body for creating a new task list
 */
export interface CreateTaskListRequest {
  title: string
}

/**
 * Request body for updating a task list
 */
export interface UpdateTaskListRequest {
  title: string
}

/**
 * Request body for creating a new task
 */
export interface CreateTaskRequest {
  title: string
  notes?: string
  due?: string  // RFC 3339 format
  parent?: string
}

/**
 * Request body for updating a task
 */
export interface UpdateTaskRequest {
  title?: string
  notes?: string
  due?: string  // RFC 3339 format
  status?: 'needsAction' | 'completed'
}

/**
 * Request body for toggling task completion
 */
export interface ToggleTaskCompleteRequest {
  completed: boolean
}

/**
 * Request body for moving a task
 */
export interface MoveTaskRequest {
  parent?: string
  previous?: string
}
