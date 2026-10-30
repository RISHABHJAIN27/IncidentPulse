// Load test: ramps to 25 virtual users, holds, then ramps down, with
// per-endpoint latency thresholds.
//   docker compose run --rm k6 run /scripts/load.js
import { sleep } from 'k6';
import { SLO_THRESHOLDS, resolveAll, seedIncidents, userJourney } from './lib.js';

export const options = {
  stages: [
    { duration: '1m', target: 25 },
    { duration: '3m', target: 25 },
    { duration: '30s', target: 0 },
  ],
  thresholds: Object.assign({}, SLO_THRESHOLDS, {
    'http_req_duration{name:GET /status}': ['p(95)<300'],
    'http_req_duration{name:GET /incidents}': ['p(95)<300'],
    'http_req_duration{name:POST /incidents}': ['p(95)<300'],
  }),
};

export function setup() {
  return { ids: seedIncidents(20) };
}

export default function (data) {
  userJourney(data.ids);
  sleep(Math.random() * 0.5 + 0.25);
}

export function teardown(data) {
  resolveAll(data.ids);
}
