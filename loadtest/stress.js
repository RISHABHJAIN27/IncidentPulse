// Capacity test: raises the request rate step by step to find where latency
// breaks the 300 ms SLO. Read the per-stage results to size replicas:
// sustainable rate per replica = highest rate that still met p95 < 300 ms.
//   docker compose run --rm k6 run /scripts/stress.js
import { seedIncidents, userJourney } from './lib.js';

const MAX_RATE = Number(__ENV.MAX_RATE || 200);

export const options = {
  scenarios: {
    ramping_rate: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 50,
      maxVUs: 300,
      stages: [
        { duration: '1m', target: Math.round(MAX_RATE * 0.25) },
        { duration: '1m', target: Math.round(MAX_RATE * 0.5) },
        { duration: '1m', target: Math.round(MAX_RATE * 0.75) },
        { duration: '1m', target: MAX_RATE },
        { duration: '30s', target: 0 },
      ],
    },
  },
  // Reported, not enforced: finding the limit is the point of this test.
  thresholds: {
    http_req_duration: [{ threshold: 'p(95)<300', abortOnFail: false }],
    http_req_failed: [{ threshold: 'rate<0.005', abortOnFail: false }],
  },
};

export function setup() {
  return { ids: seedIncidents(20) };
}

export default function (data) {
  userJourney(data.ids);
}
