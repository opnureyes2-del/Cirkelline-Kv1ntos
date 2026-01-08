// IndexedDB service for local data storage
// Uses idb library for Promise-based IndexedDB access

import { openDB, DBSchema, IDBPDatabase } from 'idb';
import type {
  LocalMemory,
  LocalSession,
  LocalKnowledgeChunk,
  PendingTask,
} from '../types';

// Database schema definition
interface ClaDBSchema extends DBSchema {
  memories: {
    key: string;
    value: LocalMemory;
    indexes: {
      'by-sync-status': number;
      'by-topic': string;
      'by-importance': number;
      'by-updated': string;
    };
  };
  sessions: {
    key: string;
    value: LocalSession;
    indexes: {
      'by-sync-status': number;
      'by-type': string;
      'by-updated': string;
    };
  };
  knowledge: {
    key: string;
    value: LocalKnowledgeChunk;
    indexes: {
      'by-source': string;
      'by-priority': number;
      'by-expires': string;
    };
  };
  tasks: {
    key: string;
    value: PendingTask;
    indexes: {
      'by-status': string;
      'by-priority': number;
      'by-type': string;
    };
  };
  embeddings: {
    key: string;
    value: {
      id: string;
      content_hash: string;
      embedding: number[];
      model: string;
      created_at: string;
    };
    indexes: {
      'by-hash': string;
    };
  };
  sync_log: {
    key: string;
    value: {
      id: string;
      operation: 'create' | 'update' | 'delete';
      entity_type: string;
      entity_id: string;
      timestamp: string;
      synced: boolean;
      error?: string;
    };
    indexes: {
      'by-synced': number;
      'by-entity': string;
    };
  };
}

const DB_NAME = 'cirkelline-cla';
const DB_VERSION = 1;

let dbInstance: IDBPDatabase<ClaDBSchema> | null = null;

/**
 * Initialize and get database connection
 */
export async function getDatabase(): Promise<IDBPDatabase<ClaDBSchema>> {
  if (dbInstance) {
    return dbInstance;
  }

  dbInstance = await openDB<ClaDBSchema>(DB_NAME, DB_VERSION, {
    upgrade(db, oldVersion, newVersion, _transaction) {
      console.log(`Upgrading database from v${oldVersion} to v${newVersion}`);

      // Memories store
      if (!db.objectStoreNames.contains('memories')) {
        const memoriesStore = db.createObjectStore('memories', { keyPath: 'id' });
        memoriesStore.createIndex('by-sync-status', 'pending_sync');
        memoriesStore.createIndex('by-topic', 'topics', { multiEntry: true });
        memoriesStore.createIndex('by-importance', 'importance');
        memoriesStore.createIndex('by-updated', 'updated_at');
      }

      // Sessions store
      if (!db.objectStoreNames.contains('sessions')) {
        const sessionsStore = db.createObjectStore('sessions', { keyPath: 'id' });
        sessionsStore.createIndex('by-sync-status', 'pending_sync');
        sessionsStore.createIndex('by-type', 'session_type');
        sessionsStore.createIndex('by-updated', 'updated_at');
      }

      // Knowledge store
      if (!db.objectStoreNames.contains('knowledge')) {
        const knowledgeStore = db.createObjectStore('knowledge', { keyPath: 'id' });
        knowledgeStore.createIndex('by-source', 'source_id');
        knowledgeStore.createIndex('by-priority', 'priority');
        knowledgeStore.createIndex('by-expires', 'expires_at');
      }

      // Tasks store
      if (!db.objectStoreNames.contains('tasks')) {
        const tasksStore = db.createObjectStore('tasks', { keyPath: 'id' });
        tasksStore.createIndex('by-status', 'status');
        tasksStore.createIndex('by-priority', 'priority');
        tasksStore.createIndex('by-type', 'task_type');
      }

      // Embeddings cache store
      if (!db.objectStoreNames.contains('embeddings')) {
        const embeddingsStore = db.createObjectStore('embeddings', { keyPath: 'id' });
        embeddingsStore.createIndex('by-hash', 'content_hash');
      }

      // Sync log store
      if (!db.objectStoreNames.contains('sync_log')) {
        const syncLogStore = db.createObjectStore('sync_log', { keyPath: 'id' });
        syncLogStore.createIndex('by-synced', 'synced');
        syncLogStore.createIndex('by-entity', 'entity_id');
      }
    },
    blocked() {
      console.warn('Database upgrade blocked by another connection');
    },
    blocking() {
      console.warn('Current connection is blocking database upgrade');
      dbInstance?.close();
      dbInstance = null;
    },
  });

  return dbInstance;
}

// ============ Memory Operations ============

export async function saveMemory(memory: LocalMemory): Promise<void> {
  const db = await getDatabase();
  await db.put('memories', memory);

  // Log sync operation
  await logSyncOperation('create', 'memory', memory.id);
}

export async function getMemory(id: string): Promise<LocalMemory | undefined> {
  const db = await getDatabase();
  return db.get('memories', id);
}

export async function getAllMemories(): Promise<LocalMemory[]> {
  const db = await getDatabase();
  return db.getAll('memories');
}

export async function getMemoriesByTopic(topic: string): Promise<LocalMemory[]> {
  const db = await getDatabase();
  return db.getAllFromIndex('memories', 'by-topic', topic);
}

export async function getPendingSyncMemories(): Promise<LocalMemory[]> {
  const db = await getDatabase();
  return db.getAllFromIndex('memories', 'by-sync-status', 1);
}

export async function deleteMemory(id: string): Promise<void> {
  const db = await getDatabase();
  await db.delete('memories', id);
  await logSyncOperation('delete', 'memory', id);
}

export async function markMemorySynced(id: string, cloudId: string): Promise<void> {
  const db = await getDatabase();
  const memory = await db.get('memories', id);
  if (memory) {
    memory.pending_sync = false;
    memory.synced_at = new Date().toISOString();
    memory.cloud_id = cloudId;
    await db.put('memories', memory);
  }
}

// ============ Session Operations ============

export async function saveSession(session: LocalSession): Promise<void> {
  const db = await getDatabase();
  await db.put('sessions', session);
  await logSyncOperation('create', 'session', session.id);
}

export async function getSession(id: string): Promise<LocalSession | undefined> {
  const db = await getDatabase();
  return db.get('sessions', id);
}

export async function getAllSessions(): Promise<LocalSession[]> {
  const db = await getDatabase();
  return db.getAll('sessions');
}

export async function getRecentSessions(limit: number = 10): Promise<LocalSession[]> {
  const db = await getDatabase();
  const all = await db.getAllFromIndex('sessions', 'by-updated');
  return all.reverse().slice(0, limit);
}

export async function deleteSession(id: string): Promise<void> {
  const db = await getDatabase();
  await db.delete('sessions', id);
  await logSyncOperation('delete', 'session', id);
}

// ============ Knowledge Operations ============

export async function saveKnowledgeChunk(chunk: LocalKnowledgeChunk): Promise<void> {
  const db = await getDatabase();
  await db.put('knowledge', chunk);
}

export async function getKnowledgeChunk(id: string): Promise<LocalKnowledgeChunk | undefined> {
  const db = await getDatabase();
  return db.get('knowledge', id);
}

export async function getKnowledgeBySource(sourceId: string): Promise<LocalKnowledgeChunk[]> {
  const db = await getDatabase();
  return db.getAllFromIndex('knowledge', 'by-source', sourceId);
}

export async function getHighPriorityKnowledge(minPriority: number = 5): Promise<LocalKnowledgeChunk[]> {
  const db = await getDatabase();
  const all = await db.getAll('knowledge');
  return all.filter(k => k.priority >= minPriority);
}

export async function cleanExpiredKnowledge(): Promise<number> {
  const db = await getDatabase();
  const now = new Date().toISOString();
  const all = await db.getAll('knowledge');
  let deleted = 0;

  for (const chunk of all) {
    if (chunk.expires_at && chunk.expires_at < now) {
      await db.delete('knowledge', chunk.id);
      deleted++;
    }
  }

  return deleted;
}

// ============ Task Operations ============

export async function queueTask(task: PendingTask): Promise<void> {
  const db = await getDatabase();
  await db.put('tasks', task);
}

export async function getTask(id: string): Promise<PendingTask | undefined> {
  const db = await getDatabase();
  return db.get('tasks', id);
}

export async function getNextTask(): Promise<PendingTask | undefined> {
  const db = await getDatabase();
  const queued = await db.getAllFromIndex('tasks', 'by-status', 'Queued');

  if (queued.length === 0) return undefined;

  // Sort by priority (descending) and created_at (ascending)
  queued.sort((a, b) => {
    if (a.priority !== b.priority) {
      return b.priority - a.priority;
    }
    return a.created_at.localeCompare(b.created_at);
  });

  return queued[0];
}

export async function updateTaskStatus(
  id: string,
  status: PendingTask['status']
): Promise<void> {
  const db = await getDatabase();
  const task = await db.get('tasks', id);
  if (task) {
    task.status = status;
    await db.put('tasks', task);
  }
}

export async function deleteTask(id: string): Promise<void> {
  const db = await getDatabase();
  await db.delete('tasks', id);
}

export async function getTasksByType(type: string): Promise<PendingTask[]> {
  const db = await getDatabase();
  return db.getAllFromIndex('tasks', 'by-type', type);
}

// ============ Embedding Cache Operations ============

export async function getCachedEmbedding(
  contentHash: string
): Promise<number[] | undefined> {
  const db = await getDatabase();
  const results = await db.getAllFromIndex('embeddings', 'by-hash', contentHash);
  return results[0]?.embedding;
}

export async function cacheEmbedding(
  contentHash: string,
  embedding: number[],
  model: string
): Promise<void> {
  const db = await getDatabase();
  await db.put('embeddings', {
    id: crypto.randomUUID(),
    content_hash: contentHash,
    embedding,
    model,
    created_at: new Date().toISOString(),
  });
}

// ============ Sync Log Operations ============

async function logSyncOperation(
  operation: 'create' | 'update' | 'delete',
  entityType: string,
  entityId: string
): Promise<void> {
  const db = await getDatabase();
  await db.put('sync_log', {
    id: crypto.randomUUID(),
    operation,
    entity_type: entityType,
    entity_id: entityId,
    timestamp: new Date().toISOString(),
    synced: false,
  });
}

export async function getPendingSyncOperations(): Promise<
  Array<{
    id: string;
    operation: string;
    entity_type: string;
    entity_id: string;
    timestamp: string;
  }>
> {
  const db = await getDatabase();
  return db.getAllFromIndex('sync_log', 'by-synced', 0);
}

export async function markSyncOperationComplete(id: string): Promise<void> {
  const db = await getDatabase();
  const log = await db.get('sync_log', id);
  if (log) {
    log.synced = true;
    await db.put('sync_log', log);
  }
}

// ============ Utility Functions ============

/**
 * Clear all data from the database
 */
export async function clearDatabase(): Promise<void> {
  const db = await getDatabase();
  await Promise.all([
    db.clear('memories'),
    db.clear('sessions'),
    db.clear('knowledge'),
    db.clear('tasks'),
    db.clear('embeddings'),
    db.clear('sync_log'),
  ]);
}

/**
 * Get database statistics
 */
export async function getDatabaseStats(): Promise<{
  memories: number;
  sessions: number;
  knowledge: number;
  tasks: number;
  embeddings: number;
  pendingSync: number;
}> {
  const db = await getDatabase();

  const [memories, sessions, knowledge, tasks, embeddings, pendingSync] =
    await Promise.all([
      db.count('memories'),
      db.count('sessions'),
      db.count('knowledge'),
      db.count('tasks'),
      db.count('embeddings'),
      db.countFromIndex('sync_log', 'by-synced', 0),
    ]);

  return { memories, sessions, knowledge, tasks, embeddings, pendingSync };
}

/**
 * Hash content for embedding cache lookup
 */
export function hashContent(content: string): string {
  // Simple hash for content deduplication
  let hash = 0;
  for (let i = 0; i < content.length; i++) {
    const char = content.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return hash.toString(16);
}

/**
 * Semantic search using local embeddings
 */
export async function searchByEmbedding(
  queryEmbedding: number[],
  topK: number = 10
): Promise<Array<{ id: string; score: number; content: string }>> {
  const db = await getDatabase();
  const memories = await db.getAll('memories');

  // Calculate cosine similarity for each memory with embedding
  const results = memories
    .filter((m) => m.embedding_local && m.embedding_local.length > 0)
    .map((m) => ({
      id: m.id,
      content: m.content,
      score: cosineSimilarity(queryEmbedding, m.embedding_local!),
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);

  return results;
}

/**
 * Calculate cosine similarity between two vectors
 */
function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) return 0;

  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }

  const denominator = Math.sqrt(normA) * Math.sqrt(normB);
  return denominator === 0 ? 0 : dotProduct / denominator;
}
