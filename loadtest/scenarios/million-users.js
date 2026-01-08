/**
 * Million Users Simulation
 *
 * Simulates traffic patterns for 1,000,000 potential users.
 * Assumes:
 *   - 1% active at any time = 10,000 concurrent users
 *   - Each user makes ~1 request per 30 seconds average
 *   - Mix of operations weighted by real-world usage
 *
 * Run: k6 run loadtest/scenarios/million-users.js
 */

import { sleep } from 'k6';
import { Trend } from 'k6/metrics';
import { config } from '../config.js';
import {
  authenticate,
  healthCheck,
  sendChat,
  getSessions,
  getConfig,
  getRandomMessage,
  randomDelay,
} from '../lib/helpers.js';

// Custom metrics for million-user test
const concurrentUsers = new Trend('concurrent_users_active');
const requestsPerSecond = new Trend('requests_per_second');

export const options = {
  scenarios: {
    // Simulate 10,000 concurrent users (1% of 1M)
    million_users: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        // Ramp up to full capacity over 10 minutes
        { duration: '2m', target: 1000 },
        { duration: '3m', target: 2500 },
        { duration: '5m', target: 5000 },
        { duration: '5m', target: 7500 },
        { duration: '5m', target: 10000 },

        // Sustain peak load
        { duration: '15m', target: 10000 },

        // Gradual ramp down
        { duration: '5m', target: 5000 },
        { duration: '5m', target: 0 },
      ],
    },
  },
  thresholds: {
    // Adjusted for scale
    http_req_duration: ['p(95)<5000', 'p(99)<15000'],
    http_req_failed: ['rate<0.02'], // 2% error rate acceptable at scale

    // Custom thresholds
    health_check_duration: ['p(95)<500'],
    auth_duration: ['p(95)<2000'],
    chat_duration: ['p(95)<60000'],
  },
};

const baseUrl = config.baseUrl;
const testUser = config.testUser;

// Shared token management
let cachedToken = null;
let tokenExpiry = 0;

function getToken() {
  const now = Date.now();
  if (cachedToken && now < tokenExpiry) {
    return cachedToken;
  }
  cachedToken = authenticate(baseUrl, testUser.email, testUser.password);
  tokenExpiry = now + (6 * 24 * 60 * 60 * 1000);
  return cachedToken;
}

export function setup() {
  console.log('='.repeat(60));
  console.log('MILLION USERS SIMULATION');
  console.log('='.repeat(60));
  console.log('Target: 1,000,000 users');
  console.log('Concurrent: 10,000 (1% active)');
  console.log('Duration: ~45 minutes');
  console.log('='.repeat(60));

  const healthy = healthCheck(baseUrl);
  if (!healthy) {
    throw new Error('System health check failed - cannot proceed');
  }

  const token = authenticate(baseUrl, testUser.email, testUser.password);
  if (!token) {
    throw new Error('Authentication failed - cannot proceed');
  }

  return { initialToken: token };
}

export default function (data) {
  const token = getToken();
  if (!token) {
    sleep(1);
    return;
  }

  // Track concurrency
  concurrentUsers.add(__VU);

  // Realistic operation distribution
  const operation = Math.random();

  if (operation < 0.30) {
    // 30% - Health/status checks (very common)
    healthCheck(baseUrl);
    sleep(randomDelay(500, 2000) / 1000);
  } else if (operation < 0.50) {
    // 20% - Config/metadata reads
    getConfig(baseUrl);
    sleep(randomDelay(500, 1500) / 1000);
  } else if (operation < 0.70) {
    // 20% - Session/history browsing
    getSessions(baseUrl, token);
    sleep(randomDelay(1000, 3000) / 1000);
  } else if (operation < 0.95) {
    // 25% - Normal chat messages
    sendChat(baseUrl, token, getRandomMessage(), 'ee461076-8cbb-4626-947b-956f293cf7bf');
    sleep(randomDelay(5000, 15000) / 1000);
  } else {
    // 5% - Deep research (expensive)
    sendChat(baseUrl, token, getRandomMessage(), 'ee461076-8cbb-4626-947b-956f293cf7bf', true);
    sleep(randomDelay(10000, 30000) / 1000);
  }
}

export function teardown(data) {
  console.log('='.repeat(60));
  console.log('MILLION USERS SIMULATION COMPLETED');
  console.log('='.repeat(60));
}
