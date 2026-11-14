import test from 'node:test';
import assert from 'node:assert/strict';
import { checkAtsResumeFit } from '../dist/ats_checker.js';

const jd = `Lio seeks a full-time IT Administration & Automation Manager. The role automates
onboarding, offboarding, access management, and device provisioning, builds internal tools
with Python and APIs, and requires identity and access management, cloud environments,
IT security, systems engineering or IT operations, and documentation.`;

test('generic ATS does not call a clearly underqualified applicant ready', () => {
  const result = checkAtsResumeFit({
    company_name: 'Lio', job_title: 'IT Administration & Automation Manager',
    job_description: jd,
    resume_text: `# Riley Example\n## Target Role\nIT Administration & Automation Manager\n
## Overview\nI documented a mock intake workflow and checked spreadsheet totals.
I have no claimed IT administration, scripting, access-management, or security-engineering experience.
## Skills\n- Documentation\n- Communication\n- Analysis\n
## Review Notes\nDo not add Python, APIs, cloud, or IAM as experience.`,
  });
  assert.equal(result.calibration.profile, 'generic');
  assert.ok(result.score < 45, `false-positive ATS score: ${result.score}`);
  assert.equal(result.readiness_label, 'blocked');
  for (const key of ['IT Administration', 'Python', 'Access Management', 'Cloud']) {
    assert.ok(result.missing_keywords.some((item) => item.term === key), `missing ${key} gap`);
    assert.ok(!result.matched_keywords.some((item) => item.term === key), `negated ${key} counted as match`);
  }
});

test('generic ATS still rewards affirmative specialist evidence', () => {
  const result = checkAtsResumeFit({
    job_description: jd,
    resume_text: 'I built Python and API internal tools for IT administration, onboarding automation, access management, and cloud security. I documented device provisioning.',
  });
  assert.ok(result.score > 45, `affirmative score too low: ${result.score}`);
  assert.ok(result.matched_keywords.some((item) => item.term === 'Python'));
  assert.ok(result.matched_keywords.some((item) => item.term === 'IT Administration'));
  assert.ok(result.score <= 74);
  assert.ok(result.ats_risks.some((item) => item.type === 'calibration_limited'));
});

test('a real-profile gap statement is not treated as specialist experience', () => {
  const result = checkAtsResumeFit({
    job_description: jd,
    resume_text: 'I improved supplier onboarding workflows and documentation. Not an IT administrator; no claim of hands-on IAM, Python scripting, cloud administration, firewall, or device management.',
  });
  assert.ok(result.matched_keywords.some((item) => item.term === 'Onboarding'));
  assert.ok(result.matched_keywords.some((item) => item.term === 'Documentation'), 'sentence-final evidence must count');
  for (const key of ['Python', 'Scripting', 'Identity and Access Management', 'Cloud', 'Device Provisioning']) {
    assert.ok(!result.matched_keywords.some((item) => item.term === key), `negated ${key} counted as match`);
  }
  assert.ok(result.score < 30, `gap statement inflated score to ${result.score}`);
});

test('unknown occupation cannot receive a ready verdict from three fallback words', () => {
  const result = checkAtsResumeFit({
    job_description: 'A specialist role in an unmodeled field.',
    resume_text: 'Communication, documentation, and analysis.',
  });
  assert.equal(result.calibration.profile, 'generic');
  assert.ok(result.score <= 74);
  assert.notEqual(result.readiness_label, 'ready');
  const lowerTarget = checkAtsResumeFit({
    job_description: 'A specialist role in an unmodeled field.',
    resume_text: 'Communication, documentation, and analysis.',
    target_score: 50,
  });
  assert.ok(lowerTarget.score < 50);
  assert.notEqual(lowerTarget.readiness_label, 'ready');
});
