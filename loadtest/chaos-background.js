// Steady background traffic for chaos experiments: a constant request rate,
// so the error ratio during the fault is measured against real load.
// Thresholds are the SLOs, so the experiment fails if users would have noticed.
//   DURATION=2m RATE=20 k6 run loadtest/chaos-background.js
import { SLO_THRESHOLDS, seedIncidents, userJourney } from './lib.js';

export const options = {
  scenarios: {
    steady: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.RATE || 20),
      timeUnit: '1s',
      duration: __ENV.DURATION || '2m',
      preAllocatedVUs: 20,
      maxVUs: 100,
    },
  },
  thresholds: SLO_THRESHOLDS,
};

export function setup() {
  return { ids: seedIncidents(10) };
}

export default function (data) {
  userJourney(data.ids);
}
