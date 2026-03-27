# AGENTS.md

This file provides guidance to Agent Ai when working with code in this repository.

## Project Overview

This is a **Minimalist CV/Resume web application** built with Next.js 14, React, TypeScript, and Tailwind CSS. The app renders a clean, print-friendly CV layout with data configured in a single file.

## Skill To Use

Use [`job-search-cuong`](/Users/pmlecuong/.codex/skills/job-search-cuong/SKILL.md) for CV edits, GitHub Pages deployment, live-site verification, and Germany job-search updates.

Use [`builder-ops`](/Users/pmlecuong/.codex/skills/builder-ops/SKILL.md) when you need repo shipping, Git/GitHub operations, environment checks, or deployment diagnosis.

Use [`playwright`](/Users/pmlecuong/.codex/skills/playwright/SKILL.md) for browser validation after visible CV changes or deployment checks.

## Application Workflow

This repo now includes a CLI-first application generator under `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system`.

Use this workflow when the user asks for:
- cover-letter generation
- company-specific application packages
- CV tailoring based on a job description
- multiple CV variants for one target role

Important files:
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/README.md`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/scripts/generate_application.py`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/master_profile.json`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/evidence_library.json`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/role_profiles.json`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/data/portfolio_digest.json`
- `/Users/pmlecuong/Documents/CuongProjects/CuongCV/application-system/intakes/`

Workflow rules:
- Treat `src/data/resume-data.tsx` as the source of truth for the public CV site.
- Treat `application-system/data/*.json` as the source of truth for generated applications, cover letters, and CV variants.
- Keep the application generator aligned with the public CV facts. Do not invent new experience in tailored variants.
- When the user provides a JD or company URL, prefer creating or updating an intake JSON and then run the Python generator.
- The generator is expected to output one cover letter and four CV variants: `product_manager`, `product_owner`, `business_analyst`, and `ai_product_ops`.
- Prefer deterministic edits to the structured JSON and templates over ad hoc document rewriting.

## Commands

### Development
```bash
pnpm dev          # Start development server on http://localhost:3000
pnpm build        # Create production build
pnpm start        # Start production server
pnpm export       # Build and export static files
pnpm deploy       # Build and prepare for GitHub Pages deployment
pnpm lint         # Run Biome linting checks
pnpm lint:fix     # Run Biome linting with auto-fix
pnpm format       # Check code formatting with Biome
pnpm format:fix   # Format code with Biome
pnpm check        # Run both linting and formatting checks
pnpm check:fix    # Run both linting and formatting with auto-fix
```

### Docker Deployment
```bash
docker compose build     # Build the container
docker compose up -d     # Run the container
docker compose down      # Stop the container
```

### PM2 Production Deployment
```bash
# Automated deployment script
./scripts/pm2-start.sh    # Complete production deployment with PM2

# Manual PM2 commands
pnpm install --frozen-lockfile  # Install dependencies
pnpm build                      # Build for production
pm2 start ecosystem.config.js   # Start with PM2
pm2 save                        # Save PM2 process list
pm2 status                      # Check status
pm2 logs cv-app                 # View logs
pm2 restart cv-app              # Restart application
pm2 stop cv-app                 # Stop application
pm2 delete cv-app               # Remove from PM2
```

**PM2 Configuration**: 
- App runs on port 3125 in production
- Cluster mode with 1 instance (configurable)
- Auto-restart enabled with 512MB memory limit
- Logs stored in `./logs/` directory

**Note**: The project uses **Biome.js** for linting and formatting instead of ESLint and Prettier. Always run `pnpm check:fix` before committing to ensure code quality.

## CV Rules

- Treat `src/data/resume-data.tsx` as the single source of truth for CV content.
- Keep work dates explicit; use an end date when employment has ended.
- Keep the RouteOps side project description current: React + TypeScript travel-planning decision support with a local Fastify backend, deterministic results, and saved trip history.
- Remove stale experimental side-project entries when replacing them.
- Keep the public CV aligned with `https://nlcuong85.github.io/cuongcv/` and the GitHub Pages workflow on `main`.
- Verify the live site after any user-visible CV change.

## Architecture

### Project Structure
- **`/src/app/`** - Next.js App Router pages and layouts
- **`/src/components/`** - Reusable UI components (using shadcn/ui)
- **`/src/data/resume-data.tsx`** - Single configuration file for all CV content
- **`/src/apollo/`** - GraphQL server setup with resolvers and type definitions
- **`/src/images/logos/`** - Company logo components

### Key Technologies
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript with decorators enabled
- **Styling**: Tailwind CSS with custom theme extensions
- **UI Components**: shadcn/ui (Radix UI based)
- **GraphQL**: Apollo Server with type-graphql at `/graphql` endpoint
- **Command Palette**: cmdk library for keyboard navigation
- **Print Optimization**: Custom print styles in global CSS

### Important Files
- **`src/data/resume-data.tsx`** - Main configuration file containing all CV data (personal info, work experience, education, skills, projects)
- **`src/app/page.tsx`** - Main resume page component that renders the CV
- **`src/app/layout.tsx`** - Root layout with metadata and analytics
- **`src/components/command-menu.tsx`** - Keyboard shortcuts (Cmd+K) for navigation
- **`src/components/print-drawer.tsx`** - Print functionality component

## Development Notes

### Adding New Sections
To add new sections to the CV, modify the `RESUME_DATA` object in `src/data/resume-data.tsx`. The layout automatically adjusts based on the data provided.

### Working On The CV
- Prefer data-only edits in `src/data/resume-data.tsx`.
- Update components only when layout, spacing, or render behavior must change.
- Use the current public email and profile details from the CV data file.
- Check print layout when changing section order or content length.
- For job-application artifacts, prefer editing `application-system/data/` and `application-system/templates/` instead of hardcoding company-specific text into the website.

### GraphQL API
The app exposes a GraphQL endpoint at `/graphql` that serves the resume data. This can be used to integrate the CV data with other applications.

### Print Optimization
The app includes special print styles to ensure the CV looks good when printed. Test print functionality when making layout changes.

### Deployment
The app is optimized for multiple deployment options:

1. **Vercel** (Recommended) - Optimized for Next.js applications
2. **GitHub Pages** - Static export with automated deployment
   - Configured with Next.js static export (`output: 'export'`)
   - Automated deployment via GitHub Actions on push to main
   - Available at: `https://nlcuong85.github.io/cuongcv/`
   - Manual deployment: `pnpm deploy`
3. **PM2** - Production deployment with process management
   - Uses `ecosystem.config.js` for configuration
   - Runs on port 3125 with cluster mode
   - Includes automated deployment script at `scripts/pm2-start.sh`
4. **Docker** - Containerized deployment for any environment

For PM2 deployment, ensure you have Node.js, pnpm, and PM2 installed on your server.
