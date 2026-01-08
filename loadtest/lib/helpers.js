import http from 'k6/http';
import { check } from 'k6';
import { Trend, Counter, Rate } from 'k6/metrics';

// Custom metrics
export const healthCheckDuration = new Trend('health_check_duration');
export const authDuration = new Trend('auth_duration');
export const chatDuration = new Trend('chat_duration');
export const errorRate = new Rate('errors');
export const successfulLogins = new Counter('successful_logins');
export const failedLogins = new Counter('failed_logins');
export const chatMessages = new Counter('chat_messages');

/**
 * Authenticate and get JWT token
 */
export function authenticate(baseUrl, email, password) {
  const loginUrl = `${baseUrl}/api/auth/login`;
  const payload = JSON.stringify({
    email: email,
    password: password,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const startTime = Date.now();
  const response = http.post(loginUrl, payload, params);
  const duration = Date.now() - startTime;

  authDuration.add(duration);

  const success = check(response, {
    'login successful': (r) => r.status === 200,
    'token received': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.token !== undefined;
      } catch {
        return false;
      }
    },
  });

  if (success) {
    successfulLogins.add(1);
    const body = JSON.parse(response.body);
    return body.token;
  } else {
    failedLogins.add(1);
    errorRate.add(1);
    return null;
  }
}

/**
 * Health check
 */
export function healthCheck(baseUrl) {
  const startTime = Date.now();
  const response = http.get(`${baseUrl}/health`);
  const duration = Date.now() - startTime;

  healthCheckDuration.add(duration);

  const success = check(response, {
    'health check passed': (r) => r.status === 200,
    'health response valid': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.status === 'healthy';
      } catch {
        return false;
      }
    },
  });

  if (!success) {
    errorRate.add(1);
  }

  return success;
}

/**
 * Send chat message
 */
export function sendChat(baseUrl, token, message, userId, deepResearch = false) {
  const chatUrl = `${baseUrl}/teams/cirkelline/runs`;

  const formData = {
    message: message,
    user_id: userId,
    stream: 'false',
    deep_research: deepResearch.toString(),
  };

  const params = {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  };

  const startTime = Date.now();
  const response = http.post(chatUrl, formData, params);
  const duration = Date.now() - startTime;

  chatDuration.add(duration);
  chatMessages.add(1);

  const success = check(response, {
    'chat response received': (r) => r.status === 200,
    'chat has content': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.content !== undefined || body.response !== undefined;
      } catch {
        return r.body && r.body.length > 0;
      }
    },
  });

  if (!success) {
    errorRate.add(1);
  }

  return { success, response, duration };
}

/**
 * Get user sessions
 */
export function getSessions(baseUrl, token) {
  const params = {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  };

  const response = http.get(`${baseUrl}/api/sessions`, params);

  const success = check(response, {
    'sessions retrieved': (r) => r.status === 200,
  });

  if (!success) {
    errorRate.add(1);
  }

  return { success, response };
}

/**
 * Get config
 */
export function getConfig(baseUrl) {
  const response = http.get(`${baseUrl}/config`);

  const success = check(response, {
    'config retrieved': (r) => r.status === 200,
    'version present': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.version !== undefined;
      } catch {
        return false;
      }
    },
  });

  return { success, response };
}

/**
 * Random message generator for realistic load
 */
export function getRandomMessage() {
  const messages = [
    'Hello!',
    'What can you help me with?',
    'Tell me about yourself',
    'How does this work?',
    'Can you search for something?',
    'What is the weather today?',
    'Help me write an email',
    'Summarize this for me',
    'What are the latest news?',
    'Translate this to Danish',
  ];
  return messages[Math.floor(Math.random() * messages.length)];
}

/**
 * Random delay between requests (human-like behavior)
 */
export function randomDelay(minMs, maxMs) {
  return Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs;
}
