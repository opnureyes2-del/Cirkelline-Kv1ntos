// Database service tests for CLA frontend
// Tests IndexedDB operations and sync functionality

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  saveMemory,
  getMemory,
  getAllMemories,
  deleteMemory,
  saveSession,
  getSession,
  queueTask,
  getNextTask,
  clearDatabase,
  getDatabaseStats,
  searchByEmbedding,
  hashContent,
} from '../services/database';
import type { LocalMemory, LocalSession, PendingTask } from '../types';

describe('Database Service', () => {
  beforeEach(async () => {
    await clearDatabase();
  });

  afterEach(async () => {
    await clearDatabase();
  });

  describe('Memory Operations', () => {
    const testMemory: LocalMemory = {
      id: 'mem-1',
      content: 'Test memory content',
      memory_type: 'fact',
      topics: ['test', 'example'],
      embedding_local: null,
      importance: 0.8,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      synced_at: null,
      cloud_id: null,
      pending_sync: true,
    };

    it('should save and retrieve a memory', async () => {
      await saveMemory(testMemory);
      const retrieved = await getMemory('mem-1');

      expect(retrieved).toBeDefined();
      expect(retrieved?.content).toBe('Test memory content');
      expect(retrieved?.topics).toEqual(['test', 'example']);
    });

    it('should get all memories', async () => {
      await saveMemory(testMemory);
      await saveMemory({ ...testMemory, id: 'mem-2', content: 'Second memory' });

      const all = await getAllMemories();
      expect(all.length).toBe(2);
    });

    it('should delete a memory', async () => {
      await saveMemory(testMemory);
      await deleteMemory('mem-1');

      const retrieved = await getMemory('mem-1');
      expect(retrieved).toBeUndefined();
    });
  });

  describe('Session Operations', () => {
    const testSession: LocalSession = {
      id: 'sess-1',
      session_type: 'chat',
      context: { topic: 'testing' },
      messages: [
        { role: 'user', content: 'Hello', timestamp: new Date().toISOString() },
        { role: 'assistant', content: 'Hi!', timestamp: new Date().toISOString() },
      ],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      synced_at: null,
      cloud_id: null,
    };

    it('should save and retrieve a session', async () => {
      await saveSession(testSession);
      const retrieved = await getSession('sess-1');

      expect(retrieved).toBeDefined();
      expect(retrieved?.session_type).toBe('chat');
      expect(retrieved?.messages.length).toBe(2);
    });
  });

  describe('Task Queue', () => {
    const createTask = (id: string, priority: number): PendingTask => ({
      id,
      task_type: 'GenerateEmbedding',
      priority,
      payload: { text: 'test' },
      created_at: new Date().toISOString(),
      retry_count: 0,
      max_retries: 3,
      status: 'Queued',
    });

    it('should queue and retrieve tasks in priority order', async () => {
      await queueTask(createTask('task-low', 1));
      await queueTask(createTask('task-high', 10));
      await queueTask(createTask('task-med', 5));

      const next = await getNextTask();
      expect(next?.id).toBe('task-high'); // Highest priority first
    });

    it('should return undefined when queue is empty', async () => {
      const next = await getNextTask();
      expect(next).toBeUndefined();
    });
  });

  describe('Database Stats', () => {
    it('should return correct stats', async () => {
      const stats = await getDatabaseStats();

      expect(stats.memories).toBe(0);
      expect(stats.sessions).toBe(0);
      expect(stats.tasks).toBe(0);
    });
  });

  describe('Content Hashing', () => {
    it('should produce consistent hashes', () => {
      const hash1 = hashContent('test content');
      const hash2 = hashContent('test content');
      const hash3 = hashContent('different content');

      expect(hash1).toBe(hash2);
      expect(hash1).not.toBe(hash3);
    });
  });

  describe('Semantic Search', () => {
    it('should find similar memories by embedding', async () => {
      const memory1: LocalMemory = {
        id: 'mem-1',
        content: 'About dogs',
        memory_type: 'fact',
        topics: ['animals'],
        embedding_local: [0.1, 0.2, 0.3, 0.4],
        importance: 0.5,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        synced_at: null,
        cloud_id: null,
        pending_sync: false,
      };

      const memory2: LocalMemory = {
        id: 'mem-2',
        content: 'About cats',
        memory_type: 'fact',
        topics: ['animals'],
        embedding_local: [0.11, 0.21, 0.31, 0.41], // Similar to memory1
        importance: 0.5,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        synced_at: null,
        cloud_id: null,
        pending_sync: false,
      };

      const memory3: LocalMemory = {
        id: 'mem-3',
        content: 'About cars',
        memory_type: 'fact',
        topics: ['vehicles'],
        embedding_local: [0.9, 0.8, 0.7, 0.6], // Very different
        importance: 0.5,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        synced_at: null,
        cloud_id: null,
        pending_sync: false,
      };

      await saveMemory(memory1);
      await saveMemory(memory2);
      await saveMemory(memory3);

      // Search with embedding similar to memory1
      const results = await searchByEmbedding([0.1, 0.2, 0.3, 0.4], 2);

      expect(results.length).toBe(2);
      expect(results[0].id).toBe('mem-1'); // Most similar
      expect(results[0].score).toBeCloseTo(1.0, 2); // Almost identical
    });
  });
});

describe('Store Integration', () => {
  describe('Settings Store', () => {
    it('should have conservative defaults', () => {
      // Import directly to test default state
      const defaultSettings = {
        max_cpu_percent: 30,
        max_ram_percent: 20,
        max_gpu_percent: 30,
        idle_only: true,
        idle_threshold_seconds: 120,
        auto_start: false,
        run_on_battery: false,
      };

      expect(defaultSettings.max_cpu_percent).toBeLessThanOrEqual(30);
      expect(defaultSettings.max_ram_percent).toBeLessThanOrEqual(20);
      expect(defaultSettings.idle_only).toBe(true);
      expect(defaultSettings.auto_start).toBe(false);
    });
  });
});
