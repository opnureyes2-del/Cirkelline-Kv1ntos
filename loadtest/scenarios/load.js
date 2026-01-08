/**
 * Load Test
 *
 * Simulates normal expected load patterns.
 * Run: k6 run loadtest/scenarios/load.js
 */

import { sleep } from 'k6';
import { SharedArray } from 'k6/data';
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

export const options = {
  scenarios: {
    load: config.scenarios.load,
  },
  thresholds: config.thresholds,
};

const baseUrl = config.baseUrl;
const testUser = config.testUser;

// Token cache
let cachedToken = null;
let tokenExpiry = 0;

function getToken() {
  const now = Date.now();
  if (cachedToken && now < tokenExpiry) {
    return cachedToken;
  }

  cachedToken = authenticate(baseUrl, testUser.email, testUser.password);
  tokenExpiry = now + (6 * 24 * 60 * 60 * 1000); // 6 days
  return cachedToken;
}

export function setup() {
  // Verify system is up
  const healthy = healthCheck(baseUrl);
  if (!healthy) {
    throw new Error('System health check failed');
  }

  // Initial auth
  const token = authenticate(baseUrl, testUser.email, testUser.password);
  if (!token) {
    throw new Error('Authentication failed');
  }

  return { initialToken: token };
}

export default function (data) {
  const token = getToken();
  if (!token) {
    console.error('Failed to get token');
    return;
  }

  // Realistic user journey
  const journey = Math.random();

  if (journey < 0.4) {
    // 40% - Quick health/config check
    healthCheck(baseUrl);
    sleep(randomDelay(500, 1500) / 1000);
  } else if (journey < 0.7) {
    // 30% - Browse sessions
    getSessions(baseUrl, token);
    sleep(randomDelay(1000, 3000) / 1000);
  } else {
    // 30% - Send chat message
    sendChat(baseUrl, token, getRandomMessage(), 'ee461076-8cbb-4626-947b-956f293cf7bf');
    sleep(randomDelay(3000, 8000) / 1000);
  }
}

export function teardown(data) {
  console.log('Load test completed');
}
