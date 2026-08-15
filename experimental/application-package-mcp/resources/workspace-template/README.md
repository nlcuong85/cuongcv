# Your Application Workspace

This folder stays on your computer. It helps your AI agent make a CV and cover letter that use your real experience.

## What you should provide

1. Put your current CV in `candidate/source/` as PDF, DOCX, or HTML. If you do not have one, give the AI a LinkedIn export, profile notes, or structured education/work history so it can build the first CV source locally.
2. Tell the AI whether you are doing a Bachelor, Master, Ausbildung/job training, school program, or another path.
3. Put a job description or job URL in `jobs/<company-role>/`.
4. For each employer, try to write 10 real bullets in your own words; 15 is even better. These are private source notes, not final CV text.
5. When the local agent offers it, add old cover letters, portfolio notes, self-written user stories, emails/letters, IELTS writing, PRDs, BRDs, work descriptions, personal statements, reports, notes, or writing samples under `voice/writing-samples/` if you want a more personal voice. Human-written samples from before ChatGPT became common are especially useful. This is optional: if you say your existing material is enough, the agent records that and stops asking.
6. The AI will ask whether you want a photo. If you provide one, it will use it; saying no is fine.
7. The AI will ask for a PNG/JPG signature for a cover letter. It can still make a letter without one.
8. The AI will ask which enclosures to list in the cover letter. Your CV/Lebenslauf is required. A diploma/transcript or previous-employer reference makes the package stronger; if you cannot provide one, the agent will not list it.

## How the MCP works

Your files stay here. The public MCP gets only selected draft text for a writing review and a small structure/version manifest. It cannot browse your computer. Its private writing-checker rules stay on the server.

## Important folders

- `candidate/source/`: original CV, optional photo and signature.
- `profile/`: verified facts and evidence.
- `voice/`: optional authentic writing samples.
- `jobs/`: each job description and intake.
- `applications/`: tailored CVs, cover letters, audits, and receipts.

## Honest quality process

The CV receives one review loop. A cover letter receives three different review loops. The agent reports weak areas honestly. It cannot guarantee an interview or prove that a document bypasses an AI detector.
