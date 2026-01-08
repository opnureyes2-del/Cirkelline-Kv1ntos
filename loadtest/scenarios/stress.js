/**
 * Stress Test
 *
 * Tests system beyond normal capacity to find limits.
 * Run: k6 run loadtest/scenarios/stress.js
 */

import { sleep } from 'k6';
import { config } from '../config.js';
import {
  authenticate,
  healthCheck,
  sendChat,
  getSessions,
  getRandomMessage,
  randomDelay,
} from '../lib/helpers.js';

export const options = {
  scenarios: {
    stress: config.scenarios.stress,
  },
  thresholds: {
    http_req_duration: ['p(95)<5000', 'p(99)<10000'],
    http_req_failed: ['rate<0.05'], // Allow up to 5% errors under stress
  },
};

const baseUrl = config.baseUrl;
const testUser = config.testUser;

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
  const healthy = healthCheck(baseUrl);
  if (!healthy) {
    throw new Error('System health check failed');
  }

  const token = authenticate(baseUrl, testUser.email, testUser.password);
  if (!token) {
    throw new Error('Authentication failed');
  }

  console.log('Starting stress test...');
  return { initialToken: token };
}

export default function (data) {
  const token = getToken();
  if (!token) return;

  // Higher proportion of expensive operations
  const operation = Math.random();

  if (operation < 0.2) {
    // 20% - Health checks
    healthCheck(baseUrl);
    sleep(randomDelay(100, 500) / 1000);
  } else if (operation < 0.4) {
    // 20% - Session reads
    getSessions(baseUrl, token);
    sleep(randomDelay(200, 1000) / 1000);
  } else {
    // 60% - Chat messages (expensive)
    sendChat(baseUrl, token, getRandomMessage(), 'ee461076-8cbb-4626-947b-956f293cf7bf');
    sleep(randomDelay(500, 2000) / 1000);
  }
}

export function teardown(data) {
  console.log('Stress test completed');
}
