/**
 * Smoke Test
 *
 * Minimal load to verify system is working correctly.
 * Run: k6 run loadtest/scenarios/smoke.js
 */

import { sleep } from 'k6';
import { config } from '../config.js';
import {
  authenticate,
  healthCheck,
  sendChat,
  getSessions,
  getConfig,
  getRandomMessage,
} from '../lib/helpers.js';

export const options = {
  scenarios: {
    smoke: config.scenarios.smoke,
  },
  thresholds: config.thresholds,
};

const baseUrl = config.baseUrl;
const testUser = config.testUser;

export function setup() {
  // Verify system is up
  const healthy = healthCheck(baseUrl);
  if (!healthy) {
    throw new Error('System health check failed');
  }

  // Authenticate
  const token = authenticate(baseUrl, testUser.email, testUser.password);
  if (!token) {
    throw new Error('Authentication failed');
  }

  console.log('Setup complete - system is healthy and auth works');
  return { token };
}

export default function (data) {
  const { token } = data;

  // 1. Health check
  healthCheck(baseUrl);
  sleep(1);

  // 2. Get config
  getConfig(baseUrl);
  sleep(1);

  // 3. Get sessions
  getSessions(baseUrl, token);
  sleep(1);

  // 4. Send a chat message
  sendChat(baseUrl, token, getRandomMessage(), 'ee461076-8cbb-4626-947b-956f293cf7bf');
  sleep(2);
}

export function teardown(data) {
  console.log('Smoke test completed');
}
