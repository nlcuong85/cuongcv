import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';

const cases = [
  ['Full-time Product Owner', 'full-time'], ['Vollzeit Product Owner', 'full-time'],
  ['Permanent full-time contract', 'full-time'], ['40 hours per week', 'full-time'],
  ['Teilzeit Analyst', 'part-time'], ['Part-time Analyst', 'part-time'],
  ['Werkstudent Marketing', 'working-student'], ['Working Student Product', 'working-student'],
  ['Studentische Hilfskraft', 'working-student'], ['Praktikum Data', 'internship'],
  ['Internship Data', 'internship'], ['Praktikantin Data', 'internship'],
  ['Product Owner with cloud expertise', null], ['Master student seeking full-time', 'full-time'],
  ['Full-time or part-time position', null], ['Vollzeit oder Teilzeit', null],
  ['Working student or internship', null], ['Werkstudent oder Praktikum', null],
  ['Open to students, full-time role', 'full-time'], ['Working student experience required for full-time role', null],
  ['Remote product manager', null], ['Contractor role', null],
  ['Full-time and Teilzeit', null], ['Intern or full-time', null],
];

for (const [text, expected] of cases) {
  test(`job type: ${text}`, () => {
    const py = `import json,sys; sys.path.insert(0,'resources/application-kit/scripts'); from job_type import classify; print(json.dumps(classify(sys.argv[1])))`;
    const result = spawnSync('python3', ['-c', py, text], { encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(JSON.parse(result.stdout).employment_type, expected);
  });
}
