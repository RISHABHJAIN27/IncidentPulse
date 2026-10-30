// Shared helpers for the Incident Pulse k6 tests.
import http from 'k6/http';
import { check } from 'k6';

export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';

const JSON_PARAMS = { headers: { 'Content-Type': 'application/json' } };
const SEVERITIES = ['low', 'medium', 'high', 'critical'];
const STATUSES = ['investigating', 'identified', 'monitoring', 'resolved'];

// Match the availability SLI: only 5xx is a failure. A 404 for an unknown
// incident is the API working correctly (docs/slo.md).
http.setResponseCallback(http.expectedStatuses({ min: 200, max: 499 }));

// The SLOs from docs/slo.md, expressed as k6 thresholds. A run that would
// break an SLO fails, which is what gates releases in CI.
export const SLO_THRESHOLDS = {
  http_req_failed: ['rate<0.005'], // availability: 99.5% non-5xx
  http_req_duration: ['p(95)<300'], // latency: 95% of requests under 300 ms
  checks: ['rate>0.99'],
};

const pick = (items) => items[Math.floor(Math.random() * items.length)];

export function createIncident() {
  const res = http.post(
    `${BASE_URL}/incidents`,
    JSON.stringify({ title: `k6 synthetic incident ${Date.now()}`, severity: pick(SEVERITIES) }),
    Object.assign({ tags: { name: 'POST /incidents' } }, JSON_PARAMS),
  );
  check(res, { 'create: 201': (r) => r.status === 201 });
  return res.status === 201 ? res.json('id') : null;
}

export function seedIncidents(count) {
  const ids = [];
  for (let i = 0; i < count; i++) {
    const id = createIncident();
    if (id) ids.push(id);
  }
  return ids;
}

// One request drawn from a realistic mix: a status page is read far more than written.
export function userJourney(ids) {
  const roll = Math.random();

  if (roll < 0.55) {
    const res = http.get(`${BASE_URL}/status`, { tags: { name: 'GET /status' } });
    check(res, { 'status: 200': (r) => r.status === 200 });
  } else if (roll < 0.8) {
    const url = Math.random() < 0.5 ? `${BASE_URL}/incidents` : `${BASE_URL}/incidents?status=investigating`;
    const res = http.get(url, { tags: { name: 'GET /incidents' } });
    check(res, { 'list: 200': (r) => r.status === 200 });
  } else if (roll < 0.93 && ids.length > 0) {
    const res = http.get(`${BASE_URL}/incidents/${pick(ids)}`, { tags: { name: 'GET /incidents/{id}' } });
    check(res, { 'get: 200': (r) => r.status === 200 });
  } else if (roll < 0.97 && ids.length > 0) {
    const res = http.patch(
      `${BASE_URL}/incidents/${pick(ids)}`,
      JSON.stringify({ status: pick(STATUSES) }),
      Object.assign({ tags: { name: 'PATCH /incidents/{id}' } }, JSON_PARAMS),
    );
    check(res, { 'update: 200': (r) => r.status === 200 });
  } else {
    createIncident();
  }
}
