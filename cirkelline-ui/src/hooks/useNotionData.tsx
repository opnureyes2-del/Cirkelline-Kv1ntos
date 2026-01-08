/**
 * Custom hook for Notion data and operations
 * Provides companies, projects, and tasks functionality
 */

import { useState, useCallback } from 'react';
import {
  NotionCompany,
  NotionProject,
  NotionTask,
  NotionDocumentation,
  CreateTaskRequest
} from '@/types/notion';

interface UseNotionDataReturn {
  // State
  companies: NotionCompany[];
  projects: NotionProject[];
  tasks: NotionTask[];
  documentation: NotionDocumentation[];
  selectedItem: NotionCompany | NotionProject | NotionTask | NotionDocumentation | null;
  loading: boolean;
  error: string | null;

  // Actions
  fetchCompanies: () => Promise<void>;
  fetchProjects: () => Promise<void>;
  fetchTasks: () => Promise<void>;
  fetchDocumentation: () => Promise<void>;
  createTask: (data: CreateTaskRequest) => Promise<boolean>;
  syncDatabases: () => Promise<{ discovered: number; stored: number }>;
  saveColumnOrder: (databaseType: 'tasks' | 'projects' | 'companies' | 'documentation', columnOrder: string[]) => Promise<boolean>;
  clearError: () => void;
  clearSelectedItem: () => void;
  selectItem: (item: NotionCompany | NotionProject | NotionTask | NotionDocumentation) => void;
}

export function useNotionData(): UseNotionDataReturn {
  const [companies, setCompanies] = useState<NotionCompany[]>([]);
  const [projects, setProjects] = useState<NotionProject[]>([]);
  const [tasks, setTasks] = useState<NotionTask[]>([]);
  const [documentation, setDocumentation] = useState<NotionDocumentation[]>([]);
  const [selectedItem, setSelectedItem] = useState<NotionCompany | NotionProject | NotionTask | NotionDocumentation | null>(null);
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
      const errorData = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`
      }));
      throw new Error(errorData.detail || 'Request failed');
    }

    return response;
  }, [apiUrl, getToken]);

  /**
   * Fetch companies from Notion - NEW DYNAMIC ENDPOINT
   */
  const fetchCompanies = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/notion/databases/companies/items');
      const data = await response.json();

      setCompanies(data.companies || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch companies';
      setError(errorMessage);
      console.error('Error fetching companies:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Fetch projects from Notion - NEW DYNAMIC ENDPOINT
   */
  const fetchProjects = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/notion/databases/projects/items');
      const data = await response.json();

      setProjects(data.projects || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch projects';
      setError(errorMessage);
      console.error('Error fetching projects:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Fetch tasks from Notion - NEW DYNAMIC ENDPOINT
   */
  const fetchTasks = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/notion/databases/tasks/items');
      const data = await response.json();

      setTasks(data.tasks || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch tasks';
      setError(errorMessage);
      console.error('Error fetching tasks:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Fetch documentation from Notion - NEW DYNAMIC ENDPOINT
   */
  const fetchDocumentation = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/notion/databases/documentation/items');
      const data = await response.json();

      setDocumentation(data.documentation || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch documentation';
      setError(errorMessage);
      console.error('Error fetching documentation:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  /**
   * Create a new task in Notion
   */
  const createTask = useCallback(async (data: CreateTaskRequest): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await authenticatedFetch('/api/notion/tasks', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      // Refresh tasks after creation
      await fetchTasks();
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create task';
      setError(errorMessage);
      console.error('Error creating task:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, fetchTasks]);

  /**
   * Sync databases from Notion
   */
  const syncDatabases = useCallback(async (): Promise<{ discovered: number; stored: number }> => {
    setLoading(true);
    setError(null);

    try {
      const response = await authenticatedFetch('/api/notion/databases/sync', {
        method: 'POST',
      });
      const data = await response.json();

      // Refresh all databases after successful sync
      await Promise.all([
        fetchCompanies(),
        fetchProjects(),
        fetchTasks(),
        fetchDocumentation()
      ]);

      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to sync databases';
      setError(errorMessage);
      console.error('Error syncing databases:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch, fetchCompanies, fetchProjects, fetchTasks, fetchDocumentation]);

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Clear selected item
   */
  const clearSelectedItem = useCallback(() => {
    setSelectedItem(null);
  }, []);

  /**
   * Select an item
   */
  const selectItem = useCallback((item: NotionCompany | NotionProject | NotionTask | NotionDocumentation) => {
    setSelectedItem(item);
  }, []);

  /**
   * Save user's custom column order for a database
   */
  const saveColumnOrder = useCallback(async (
    databaseType: 'tasks' | 'projects' | 'companies' | 'documentation',
    columnOrder: string[]
  ): Promise<boolean> => {
    setLoading(true);
    setError(null);

    try {
      await authenticatedFetch(`/api/notion/databases/${databaseType}/column-order`, {
        method: 'PUT',
        body: JSON.stringify({ column_order: columnOrder }),
      });

      console.log(`✅ Saved column order for ${databaseType}:`, columnOrder);
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save column order';
      setError(errorMessage);
      console.error('Error saving column order:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  return {
    companies,
    projects,
    tasks,
    documentation,
    selectedItem,
    loading,
    error,
    fetchCompanies,
    fetchProjects,
    fetchTasks,
    fetchDocumentation,
    createTask,
    syncDatabases,
    clearError,
    clearSelectedItem,
    selectItem,
    saveColumnOrder,
  };
}
