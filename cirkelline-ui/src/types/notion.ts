// Notion API types for frontend

export interface NotionCompany {
  id: string
  name: string
  domain?: string
  description?: string
  industry?: string
  size?: string
  status?: string
  created_time: string
  last_edited_time: string
  url: string
  [key: string]: unknown
}

export interface NotionProject {
  id: string
  name: string
  status?: string
  priority?: string
  start_date?: string
  end_date?: string
  description?: string
  company_relation?: string[]
  created_time: string
  last_edited_time: string
  url: string
  [key: string]: unknown
}

export interface NotionTask {
  id: string
  title: string
  status?: string
  priority?: string
  due_date?: string
  description?: string
  project_relation?: string[]
  assignee?: string
  created_time: string
  last_edited_time: string
  url: string
  [key: string]: unknown
}

export interface NotionDocumentation {
  id: string
  title: string
  category?: string
  tags?: string[]
  description?: string
  created_time: string
  last_edited_time: string
  url: string
  [key: string]: unknown
}

export interface CreateTaskRequest {
  title: string
  status?: string
  priority?: string
  due_date?: string
  description?: string
  project_id?: string
}

export interface NotionStatus {
  connected: boolean
  workspace_name?: string
  workspace_icon?: string
  workspace_id?: string
  owner_email?: string
}
