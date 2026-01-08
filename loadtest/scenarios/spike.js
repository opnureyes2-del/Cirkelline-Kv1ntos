/**
 * Spike Test
 *
 * Tests system response to sudden traffic spikes.
 * Run: k6 run loadtest/scenarios/spike.js
 */

import { sleep } from 'k6';
import { config } from '../config.js';
import {
  authenticate,
  healthCheck,
  sendChat,
  getRandomMessage,
  randomDelay,
} from '../lib/helpers.js';

export const options = {
  scenarios: {
    spike: config.scenarios.spike,
  },
  thresholds: {
    http_req_duration: ['p(95)<10000'],
    http_req_failed: ['rate<0.10'], // Allow up to 10% errors during spike
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

  console.log('Starting spike test - expect sudden load increases...');
  return { initialToken: token };
}

export default function (data) {
  const token = getToken();
  if (!token) return;

  // Fast operations during spike
  const operation = Math.random();

  if (operation < 0.5) {
    // 50% - Quick health checks
    healthCheck(baseUrl);
  } else {
    // 50% - Chat
    sendChat(baseUrl, token, getRandomMessage(), 'ee461076-8cbb-4626-947b-956f293cf7bf');
  }

  sleep(randomDelay(100, 500) / 1000);
}

export function teardown(data) {
  console.log('Spike test completed');
}
