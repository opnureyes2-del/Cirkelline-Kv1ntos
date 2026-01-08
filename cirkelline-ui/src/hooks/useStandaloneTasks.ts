/**
 * Custom hook for Standalone Tasks data and operations
 * Works without external connections - data stored in PostgreSQL
 * Optional Google Tasks sync when connected
 */

import { useState, useCallback } from 'react';
import {
  TaskList,
  Task,
  TaskListsResponse,
  TasksResponse,
  CreateTaskListRequest,
  UpdateTaskListRequest,
  CreateTaskRequest,
  UpdateTaskRequest,
  SyncStatus,
  SyncResult,
  TaskApiError
} from '@/types/standaloneTasks';

interface UseStandaloneTasksReturn {
  // List state
  lists: TaskList[];
  selectedListId: string | null;

  // Task state
  tasks: Task[];
  currentTask: Task | null;
  loading: boolean;
  error: string | null;

  // Google sync state
  googleConnected: boolean;
  isSyncing: boolean;
  lastSyncResult: SyncResult | null;

  // List actions
  fetchLists: (source?: 'local') => Promise<void>;
  createList: (data: CreateTaskListRequest) => Promise<TaskList | null>;
  updateList: (id: string, data: UpdateTaskListRequest) => Promise<boolean>;
  deleteList: (id: string) => Promise<boolean>;
  selectList: (id: string | null) => void;

  // Task actions
  fetchTasks: (listId?: string, completed?: boolean, source?: 'local') => Promise<void>;
  fetchTaskDetail: (taskId: string) => Promise<void>;
  createTask: (data: CreateTaskRequest) => Promise<Task | null>;
  updateTask: (taskId: string, data: UpdateTaskRequest) => Promise<boolean>;
  deleteTask: (taskId: string) => Promise<boolean>;
  toggleTaskComplete: (taskId: string) => Promise<boolean>;
  clearError: () => void;
  clearCurrentTask: () => void;

  // Google sync actions
  checkSyncStatus: () => Promise<void>;
  syncFromGoogle: () => Promise<SyncResult | null>;
  disconnectGoogle: () => Promise<boolean>;

  // Utility
  getDefaultList: () => TaskList | undefined;
  getTasksByList: (listId: string) => Task[];
  hasLists: boolean;
}

export function useStandaloneTasks(): UseStandaloneTasksReturn {
  // List state
  const [lists, setLists] = useState<TaskList[]>([]);
  const [selectedListId, setSelectedListId] = useState<string | null>(null);

  // Task state
  const [tasks, setTasks] = useState<Task[]>([]);
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Google sync state
  const [googleConnected, setGoogleConnected] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSyncResult, setLastSyncResult] = useState<SyncResult | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777';

  /**
   * Get JWT token from localStorage
   */
  const getToken = useCallback((): string | null => {
    return localStorage.getItem('token');
  }, []);

  /**
   * Generic fetch wrapper with auth
   */
  const authenticatedFetch = useCallback(async (
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> => {
    const token = getToken();
    if (!token) {
      throw new Error('Authentication required');
    }

    const response = await fetch(`${apiUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData: TaskApiError = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`
      }));
      throw new Error(errorData.detail || 'Request failed');
    }

    return response;
  }, [apiUrl, getToken]);

  // ═══════════════════════════════════════════════════════════════
  // LIST OPERATIONS
  // ═══════════════════════════════════════════════════════════════

  const fetchLists = useCallback(async (source?: 'local') => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (source) params.append('source', source);
      const endpoint = `/api/tasks/lists${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await authenticatedFetch(endpoint);
      const data: TaskListsResponse = await response.json();
      setLists(data.lists || []);

      // Select first list by default if none selected
      if (!selectedListId && data.lists.length > 0) {
        const defaultList = data.lists.find(l => l.is_default) || data.lists[0];
        setSelectedListId(defaultList.id);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch task lists';
      setError(errorMessage);
      console.error('Fetch task lists error:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, selectedListId]);

  const createList = useCallback(async (data: CreateTaskListRequest): Promise<TaskList | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/tasks/lists', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      const newList: TaskList = await response.json();
      setLists(prev => [...prev, newList]);

      // Select the new list if it's the first one
      if (lists.length === 0) {
        setSelectedListId(newList.id);
      }

      return newList;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create task list';
      setError(errorMessage);
      console.error('Create task list error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, lists.length]);

  const updateList = useCallback(async (id: string, data: UpdateTaskListRequest): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(`/api/tasks/lists/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });

      const updatedList: TaskList = await response.json();
      setLists(prev => prev.map(l => l.id === id ? updatedList : l));

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update task list';
      setError(errorMessage);
      console.error('Update task list error:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  const deleteList = useCallback(async (id: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await authenticatedFetch(`/api/tasks/lists/${id}`, {
        method: 'DELETE',
      });

      setLists(prev => prev.filter(l => l.id !== id));
      setTasks(prev => prev.filter(t => t.list_id !== id));

      // Select another list if the deleted one was selected
      if (selectedListId === id) {
        const remaining = lists.filter(l => l.id !== id);
        setSelectedListId(remaining.length > 0 ? remaining[0].id : null);
      }

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete task list';
      setError(errorMessage);
      console.error('Delete task list error:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, selectedListId, lists]);

  const selectList = useCallback((id: string | null) => {
    setSelectedListId(id);
  }, []);

  // ═══════════════════════════════════════════════════════════════
  // TASK OPERATIONS
  // ═══════════════════════════════════════════════════════════════

  const fetchTasks = useCallback(async (listId?: string, completed?: boolean, source?: 'local') => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (listId) params.append('list_id', listId);
      if (completed !== undefined) params.append('completed', String(completed));
      if (source) params.append('source', source);

      const endpoint = `/api/tasks/tasks${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await authenticatedFetch(endpoint);
      const data: TasksResponse = await response.json();
      setTasks(data.tasks || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch tasks';
      setError(errorMessage);
      console.error('Fetch tasks error:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  const fetchTaskDetail = useCallback(async (taskId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(`/api/tasks/tasks/${taskId}`);
      const task: Task = await response.json();
      setCurrentTask(task);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch task detail';
      setError(errorMessage);
      console.error('Fetch task detail error:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  const createTask = useCallback(async (data: CreateTaskRequest): Promise<Task | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/tasks/tasks', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      const newTask: Task = await response.json();
      setTasks(prev => [newTask, ...prev]);

      return newTask;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create task';
      setError(errorMessage);
      console.error('Create task error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  const updateTask = useCallback(async (taskId: string, data: UpdateTaskRequest): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(`/api/tasks/tasks/${taskId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });

      const updatedTask: Task = await response.json();
      setTasks(prev => prev.map(t => t.id === taskId ? updatedTask : t));

      if (currentTask?.id === taskId) {
        setCurrentTask(updatedTask);
      }

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update task';
      setError(errorMessage);
      console.error('Update task error:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, currentTask]);

  const deleteTask = useCallback(async (taskId: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await authenticatedFetch(`/api/tasks/tasks/${taskId}`, {
        method: 'DELETE',
      });

      setTasks(prev => prev.filter(t => t.id !== taskId));

      if (currentTask?.id === taskId) {
        setCurrentTask(null);
      }

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete task';
      setError(errorMessage);
      console.error('Delete task error:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, currentTask]);

  const toggleTaskComplete = useCallback(async (taskId: string): Promise<boolean> => {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return false;

    return updateTask(taskId, { completed: !task.completed });
  }, [tasks, updateTask]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearCurrentTask = useCallback(() => {
    setCurrentTask(null);
  }, []);

  // ═══════════════════════════════════════════════════════════════
  // GOOGLE SYNC OPERATIONS
  // ═══════════════════════════════════════════════════════════════

  const checkSyncStatus = useCallback(async () => {
    try {
      const response = await authenticatedFetch('/api/tasks/sync/status');
      const data: SyncStatus = await response.json();
      setGoogleConnected(data.google_connected);
    } catch (err) {
      console.error('Check sync status error:', err);
      setGoogleConnected(false);
    }
  }, [authenticatedFetch]);

  const syncFromGoogle = useCallback(async (): Promise<SyncResult | null> => {
    setIsSyncing(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/tasks/sync/google', {
        method: 'POST',
      });

      const result: SyncResult = await response.json();
      setLastSyncResult(result);

      // Refresh lists and tasks after sync
      await fetchLists();
      await fetchTasks();

      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to sync from Google';
      setError(errorMessage);
      console.error('Sync from Google error:', err);
      return null;
    } finally {
      setIsSyncing(false);
    }
  }, [authenticatedFetch, fetchLists, fetchTasks]);

  const disconnectGoogle = useCallback(async (): Promise<boolean> => {
    setIsSyncing(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/tasks/sync/google', {
        method: 'DELETE',
      });

      if (response.ok) {
        // Refresh lists and tasks (will only show local now)
        await fetchLists('local');
        await fetchTasks(undefined, undefined, 'local');
        return true;
      }
      return false;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to disconnect from Google';
      setError(errorMessage);
      console.error('Disconnect from Google error:', err);
      return false;
    } finally {
      setIsSyncing(false);
    }
  }, [authenticatedFetch, fetchLists, fetchTasks]);

  // ═══════════════════════════════════════════════════════════════
  // UTILITY FUNCTIONS
  // ═══════════════════════════════════════════════════════════════

  const getDefaultList = useCallback((): TaskList | undefined => {
    return lists.find(l => l.is_default) || lists[0];
  }, [lists]);

  const getTasksByList = useCallback((listId: string): Task[] => {
    return tasks.filter(t => t.list_id === listId);
  }, [tasks]);

  return {
    // List state
    lists,
    selectedListId,

    // Task state
    tasks,
    currentTask,
    loading,
    error,

    // Google sync state
    googleConnected,
    isSyncing,
    lastSyncResult,

    // List actions
    fetchLists,
    createList,
    updateList,
    deleteList,
    selectList,

    // Task actions
    fetchTasks,
    fetchTaskDetail,
    createTask,
    updateTask,
    deleteTask,
    toggleTaskComplete,
    clearError,
    clearCurrentTask,

    // Google sync actions
    checkSyncStatus,
    syncFromGoogle,
    disconnectGoogle,

    // Utility
    getDefaultList,
    getTasksByList,
    hasLists: lists.length > 0,
  };
}
