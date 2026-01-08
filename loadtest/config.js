/**
 * Cirkelline Load Test Configuration
 *
 * Environment variables:
 *   BASE_URL      - Target URL (default: http://localhost:7777)
 *   TEST_EMAIL    - Test user email
 *   TEST_PASSWORD - Test user password
 */

export const config = {
  // Target environment
  baseUrl: __ENV.BASE_URL || 'http://localhost:7777',

  // Test credentials
  testUser: {
    email: __ENV.TEST_EMAIL || 'opnureyes2@gmail.com',
    password: __ENV.TEST_PASSWORD || 'RASMUS_PASSWORD_HERE',
  },

  // Thresholds
  thresholds: {
    // Response time thresholds
    http_req_duration: ['p(95)<2000', 'p(99)<5000'],

    // Error rate threshold
    http_req_failed: ['rate<0.01'],

    // Custom thresholds
    health_check_duration: ['p(95)<100'],
    auth_duration: ['p(95)<500'],
    chat_duration: ['p(95)<30000'],
  },

  // Scenarios for different load profiles
  scenarios: {
    // Smoke test - minimal load to verify functionality
    smoke: {
      executor: 'constant-vus',
      vus: 1,
      duration: '1m',
    },

    // Load test - normal expected load
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },   // Ramp up
        { duration: '5m', target: 50 },   // Stay at 50
        { duration: '2m', target: 100 },  // Ramp to 100
        { duration: '5m', target: 100 },  // Stay at 100
        { duration: '2m', target: 0 },    // Ramp down
      ],
    },

    // Stress test - beyond normal capacity
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 100 },
        { duration: '5m', target: 100 },
        { duration: '2m', target: 200 },
        { duration: '5m', target: 200 },
        { duration: '2m', target: 300 },
        { duration: '5m', target: 300 },
        { duration: '5m', target: 0 },
      ],
    },

    // Spike test - sudden traffic spike
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 100 },
        { duration: '1m', target: 100 },
        { duration: '10s', target: 500 },
        { duration: '3m', target: 500 },
        { duration: '10s', target: 100 },
        { duration: '3m', target: 100 },
        { duration: '10s', target: 0 },
      ],
    },

    // Soak test - extended duration
    soak: {
      executor: 'constant-vus',
      vus: 50,
      duration: '30m',
    },

    // Breakpoint test - find breaking point
    breakpoint: {
      executor: 'ramping-arrival-rate',
      startRate: 1,
      timeUnit: '1s',
      preAllocatedVUs: 500,
      maxVUs: 1000,
      stages: [
        { duration: '2m', target: 10 },
        { duration: '2m', target: 50 },
        { duration: '2m', target: 100 },
        { duration: '2m', target: 200 },
        { duration: '2m', target: 300 },
        { duration: '2m', target: 400 },
        { duration: '2m', target: 500 },
      ],
    },
  },
};
