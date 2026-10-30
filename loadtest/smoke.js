// Smoke test: a few users for 30 seconds. Runs in CI on every pull request and
// fails the build if the SLOs would be broken.
//   k6 run loadtest/smoke.js            (BASE_URL defaults to http://localhost:8080)
import { sleep } from 'k6';
import { SLO_THRESHOLDS, resolveAll, seedIncidents, userJourney } from './lib.js';

export const options = {
  vus: 2,
  duration: '30s',
  thresholds: SLO_THRESHOLDS,
};

export function setup() {
  return { ids: seedIncidents(5) };
}

export default function (data) {
  userJourney(data.ids);
  sleep(0.2);
}

export function teardown(data) {
  resolveAll(data.ids);
}
