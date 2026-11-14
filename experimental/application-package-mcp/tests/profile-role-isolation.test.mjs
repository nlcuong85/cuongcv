import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

const realProfile = JSON.parse(readFileSync('../../application-system/data/master_profile.json', 'utf8'));
const fictionalProfile = { education: [{ degree: 'Bachelor of Computer Science' }], experience: [{ role: 'Working Student' }] };
const profiles = [['verified CV', realProfile], ['fictional applicant', fictionalProfile]];
const jobs = [
  ['Lio is hiring a full-time IT Administration & Automation Manager in Munich.', 'full-time'],
  ['We seek a Werkstudent for process documentation.', 'working-student'],
  ['We seek a part-time analyst.', 'part-time'],
  ['A Praktikum in product operations.', 'internship'],
  ['Open role in product operations.', null],
  ['Full-time or part-time product owner.', null],
  ['Working student or junior product analyst.', 'working-student'],
  ['Vollzeit Product Owner, remote in Germany.', 'full-time'],
];
const existingIntakes = [
  ['lio-it-administration-automation-manager', 'full-time'],
  ['mercedes-benz-insurance-services-working-student-product-owner-support-insurance-platform-of-services', 'working-student'],
  ['sap-working-student-threat-modelling-service-operation-and-automation', 'working-student'],
  ['acteno-energy-ai-meets-energy-hybrid-systems', 'internship'],
];

for (const [name, profile] of profiles) {
  for (const [jd, expected] of jobs) {
    test(`${name}: ${jd}`, () => {
      assert.ok(profile && typeof profile === 'object');
      const py = `import json,sys; sys.path.insert(0,'resources/application-kit/scripts'); from job_type import classify; print(json.dumps(classify(sys.argv[1])))`;
      const run = spawnSync('python3', ['-c', py, jd], { encoding: 'utf8' });
      assert.equal(run.status, 0, run.stderr);
      assert.equal(JSON.parse(run.stdout).employment_type, expected);
    });
  }
}

for (const [name, profile] of profiles) {
  for (const [slug, expected] of existingIntakes) {
    test(`${name}: existing JD ${slug}`, () => {
      assert.ok(profile && typeof profile === 'object');
      const intake = JSON.parse(readFileSync(`../../application-system/intakes/${slug}.json`, 'utf8'));
      const py = `import json,sys; sys.path.insert(0,'resources/application-kit/scripts'); from job_type import classify; print(json.dumps(classify(sys.argv[1])))`;
      const run = spawnSync('python3', ['-c', py, intake.job_description], { encoding: 'utf8' });
      assert.equal(run.status, 0, run.stderr);
      assert.equal(JSON.parse(run.stdout).employment_type, expected);
    });
  }
}
