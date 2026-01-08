/**
 * Standalone Tasks TypeScript Type Definitions
 * For local database storage with optional Google sync
 */

export interface TaskList {
  id: string;
  name: string;
  color: string;
  is_default: boolean;
  source: 'local' | 'google';
  external_id?: string;
  sync_enabled: boolean;
  last_synced_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Task {
  id: string;
  list_id: string;
  list_name?: string;
  list_color?: string;
  title: string;
  notes?: string;
  due_date?: string;
  completed: boolean;
  completed_at?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  position: number;
  parent_id?: string;
  external_id?: string;
  source: 'local' | 'google';
  sync_status: 'local' | 'synced' | 'pending';
  created_at?: string;
  updated_at?: string;
}

export interface TaskListsResponse {
  lists: TaskList[];
  total: number;
}

export interface TasksResponse {
  tasks: Task[];
  total: number;
}

export interface CreateTaskListRequest {
  name: string;
  color?: string;
  is_default?: boolean;
}

export interface UpdateTaskListRequest {
  name?: string;
  color?: string;
  is_default?: boolean;
}

export interface CreateTaskRequest {
  list_id: string;
  title: string;
  notes?: string;
  due_date?: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  parent_id?: string;
}

export interface UpdateTaskRequest {
  list_id?: string;
  title?: string;
  notes?: string;
  due_date?: string;
  completed?: boolean;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  position?: number;
}

export interface SyncStatus {
  google_connected: boolean;
  total_lists: number;
  synced_lists: number;
}

export interface SyncResult {
  success: boolean;
  synced_lists: number;
  synced_tasks: number;
  message: string;
}

export interface TaskApiError {
  detail: string;
}
