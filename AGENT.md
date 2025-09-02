# AGENT.md

This file provides guidance to Agent Ai when working with code in this repository.

## Project Overview

This is a **Minimalist CV/Resume web application** built with Next.js 14, React, TypeScript, and Tailwind CSS. The app renders a clean, print-friendly CV layout with data configured in a single file.

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