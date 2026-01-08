/**
 * Custom hook for Google Tasks data and operations
 * Provides task lists and tasks management functionality
 */

import { useState, useCallback } from 'react';
import {
  TaskList,
  Task,
  CreateTaskRequest,
  UpdateTaskRequest,
  MoveTaskRequest
} from '@/types/tasks';

interface ApiResponse {
  success: boolean;
  detail?: string;
}

interface UseTasksDataReturn {
  // State
  taskLists: TaskList[];
  selectedList: TaskList | null;
  tasks: Task[];
  currentTask: Task | null;
  loading: boolean;
  error: string | null;

  // Task Lists Actions
  fetchTaskLists: () => Promise<void>;
  fetchTaskListDetail: (listId: string) => Promise<void>;
  createTaskList: (title: string) => Promise<boolean>;
  updateTaskList: (listId: string, title: string) => Promise<boolean>;
  deleteTaskList: (listId: string) => Promise<boolean>;

  // Tasks Actions
  fetchTasks: (listId: string, showCompleted?: boolean) => Promise<void>;
  fetchTaskDetail: (listId: string, taskId: string) => Promise<void>;
  createTask: (listId: string, data: CreateTaskRequest) => Promise<boolean>;
  updateTask: (listId: string, taskId: string, data: UpdateTaskRequest) => Promise<boolean>;
  deleteTask: (listId: string, taskId: string) => Promise<boolean>;
  toggleTaskComplete: (listId: string, taskId: string, completed: boolean) => Promise<boolean>;
  moveTask: (listId: string, taskId: string, data: MoveTaskRequest) => Promise<boolean>;

  // Utility Actions
  setSelectedList: (list: TaskList | null) => void;
  clearError: () => void;
  clearCurrentTask: () => void;
}

export function useTasksData(): UseTasksDataReturn {
  const [taskLists, setTaskLists] = useState<TaskList[]>([]);
  const [selectedList, setSelectedListState] = useState<TaskList | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      const errorData: ApiResponse = await response.json().catch(() => ({
        success: false,
        detail: `HTTP ${response.status}: ${response.statusText}`
      }));
      throw new Error(errorData.detail || 'Request failed');
    }

    return response;
  }, [apiUrl, getToken]);

  // ═══════════════════════════════════════════════════════════════════
  // TASK LISTS OPERATIONS
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Fetch all task lists
   */
  const fetchTaskLists = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/google/tasks/lists');
      const data = await response.json();

      setTaskLists(data.task_lists || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch task lists';
      setError(errorMessage);
      console.error('Fetch task lists error:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Fetch specific task list detail
   */
  const fetchTaskListDetail = useCallback(async (listId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(`/api/google/tasks/lists/${listId}`);
      const data = await response.json();

      setSelectedListState(data.task_list);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch task list';
      setError(errorMessage);
      console.error('Fetch task list detail error:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Create a new task list
   */
  const createTaskList = useCallback(async (title: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/google/tasks/lists', {
        method: 'POST',
        body: JSON.stringify({ title }),
      });

      const data = await response.json();

      // Add new task list to state
      setTaskLists(prev => [...prev, data.task_list]);

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create task list';
      setError(errorMessage);
      console.error('Create task list error:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Update (rename) a task list
   */
  const updateTaskList = useCallback(async (listId: string, title: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(`/api/google/tasks/lists/${listId}`, {
        method: 'PUT',
        body: JSON.stringify({ title }),
      });

      const data = await response.json();

      // Update task list in state
      setTaskLists(prev => prev.map(list =>
        list.id === listId ? data.task_list : list
      ));

      // Update selected list if it's the one being updated
      if (selectedList?.id === listId) {
        setSelectedListState(data.task_list);
      }

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update task list';
      setError(errorMessage);
      console.error('Update task list error:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, selectedList]);

  /**
   * Delete a task list
   */
  const deleteTaskList = useCallback(async (listId: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await authenticatedFetch(`/api/google/tasks/lists/${listId}`, {
        method: 'DELETE',
      });

      // Remove task list from state
      setTaskLists(prev => prev.filter(list => list.id !== listId));

      // Clear selected list if it was deleted
      if (selectedList?.id === listId) {
        setSelectedListState(null);
        setTasks([]);
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
  }, [authenticatedFetch, selectedList]);

  // ═══════════════════════════════════════════════════════════════════
  // TASKS OPERATIONS
  // ═══════════════════════════════════════════════════════════════════

  /**
   * Fetch tasks in a specific task list
   */
  const fetchTasks = useCallback(async (listId: string, showCompleted: boolean = false) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        show_completed: showCompleted.toString(),
        show_deleted: 'false'
      });

      const response = await authenticatedFetch(`/api/google/tasks/lists/${listId}/tasks?${params}`);
      const data = await response.json();

      setTasks(data.tasks || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch tasks';
      setError(errorMessage);
      console.error('Fetch tasks error:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Fetch specific task detail
   */
  const fetchTaskDetail = useCallback(async (listId: string, taskId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(`/api/google/tasks/lists/${listId}/tasks/${taskId}`);
      const data = await response.json();

      setCurrentTask(data.task);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch task';
      setError(errorMessage);
      console.error('Fetch task detail error:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Create a new task
   */
  const createTask = useCallback(async (listId: string, data: CreateTaskRequest): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(`/api/google/tasks/lists/${listId}/tasks`, {
        method: 'POST',
        body: JSON.stringify(data),
      });

      const result = await response.json();

      // Add new task to state
      setTasks(prev => [result.task, ...prev]);

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create task';
      setError(errorMessage);
      console.error('Create task error:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Update a task
   */
  const updateTask = useCallback(async (
    listId: string,
    taskId: string,
    data: UpdateTaskRequest
  ): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(`/api/google/tasks/lists/${listId}/tasks/${taskId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });

      const result = await response.json();

      // Update task in state
      setTasks(prev => prev.map(task =>
        task.id === taskId ? result.task : task
      ));

      // Update current task if it's the one being updated
      if (currentTask?.id === taskId) {
        setCurrentTask(result.task);
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

  /**
   * Delete a task
   */
  const deleteTask = useCallback(async (listId: string, taskId: string): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await authenticatedFetch(`/api/google/tasks/lists/${listId}/tasks/${taskId}`, {
        method: 'DELETE',
      });

      // Remove task from state
      setTasks(prev => prev.filter(task => task.id !== taskId));

      // Clear current task if it was deleted
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

  /**
   * Toggle task completion status
   */
  const toggleTaskComplete = useCallback(async (
    listId: string,
    taskId: string,
    completed: boolean
  ): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(
        `/api/google/tasks/lists/${listId}/tasks/${taskId}/complete`,
        {
          method: 'POST',
          body: JSON.stringify({ completed }),
        }
      );

      const result = await response.json();

      // Update task in state
      setTasks(prev => prev.map(task =>
        task.id === taskId ? result.task : task
      ));

      // Update current task if it's the one being updated
      if (currentTask?.id === taskId) {
        setCurrentTask(result.task);
      }

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to toggle task completion';
      setError(errorMessage);
      console.error('Toggle task complete error:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, currentTask]);

  /**
   * Move a task (reorder or change parent)
   */
  const moveTask = useCallback(async (
    listId: string,
    taskId: string,
    data: MoveTaskRequest
  ): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch(
        `/api/google/tasks/lists/${listId}/tasks/${taskId}/move`,
        {
          method: 'POST',
          body: JSON.stringify(data),
        }
      );

      const result = await response.json();

      // Update task in state
      setTasks(prev => prev.map(task =>
        task.id === taskId ? result.task : task
      ));

      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to move task';
      setError(errorMessage);
      console.error('Move task error:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  // ═══════════════════════════════════════════════════════════════════
  // UTILITY ACTIONS
  // ═══════════════════════════════════════════════════════════════════

  const setSelectedList = useCallback((list: TaskList | null) => {
    setSelectedListState(list);
    // Clear tasks when changing lists
    if (list === null) {
      setTasks([]);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearCurrentTask = useCallback(() => {
    setCurrentTask(null);
  }, []);

  return {
    // State
    taskLists,
    selectedList,
    tasks,
    currentTask,
    loading,
    error,

    // Task Lists Actions
    fetchTaskLists,
    fetchTaskListDetail,
    createTaskList,
    updateTaskList,
    deleteTaskList,

    // Tasks Actions
    fetchTasks,
    fetchTaskDetail,
    createTask,
    updateTask,
    deleteTask,
    toggleTaskComplete,
    moveTask,

    // Utility Actions
    setSelectedList,
    clearError,
    clearCurrentTask,
  };
}
