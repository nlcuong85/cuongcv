# Cuong's Professional CV

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fnlcuong85%2Fcuongcv)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?logo=typescript)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3.4-38B2AC?logo=tailwind-css)](https://tailwindcss.com/)
[![pnpm](https://img.shields.io/badge/pnpm-8+-F69220?logo=pnpm)](https://pnpm.io/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A clean and modern web application showcasing my professional experience, skills, and achievements through a minimalist CV/Resume with a print-friendly layout. This is my personal portfolio website built with modern web technologies.

## ✨ Features

- 📝 **Single Config File** - Update all your resume data in [one place](./src/data/resume-data.tsx)
- 🎨 **Minimalist Design** - Clean, professional layout focused on content
- 📱 **Responsive** - Looks great on all devices, from mobile to desktop
- 🖨️ **Print Optimized** - Specially designed print styles for physical copies
- ⌨️ **Keyboard Navigation** - Press `Cmd/Ctrl + K` to quickly navigate through sections
- 🚀 **Fast Performance** - Built with Next.js 14 and optimized for Core Web Vitals
- 🔄 **Auto Layout** - Sections automatically adjust based on your content
- 📊 **GraphQL API** - Access your resume data programmatically at `/graphql`
- 🎯 **SEO Friendly** - Optimized metadata for better search visibility
- 🐳 **Docker Support** - Easy containerized deployment

## 🛠️ Tech Stack

- **Framework**: [Next.js 14](https://nextjs.org/) (App Router)
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **UI Components**: [shadcn/ui](https://ui.shadcn.com/) (Radix UI)
- **GraphQL**: [Apollo Server](https://www.apollographql.com/) + [TypeGraphQL](https://typegraphql.com/)
- **Package Manager**: [pnpm](https://pnpm.io/)
- **Deployment**: Optimized for [Vercel](https://vercel.com/)

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ 
- pnpm 8+

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/nlcuong85/cuongcv.git
   cd cuongcv
   ```

2. **Install dependencies**

   ```bash
   pnpm install
   ```

3. **Start the development server**

   ```bash
   pnpm dev
   ```

4. **Open [http://localhost:3000](http://localhost:3000)** in your browser

5. **Customize the CV**
   
   The CV is already customized with my personal information, but you can view and modify the data in [src/data/resume-data.tsx](./src/data/resume-data.tsx) to see how it's structured.

### Available Scripts

```bash
pnpm dev          # Start development server
pnpm build        # Build for production
pnpm start        # Start production server
pnpm lint         # Run ESLint
```

## 📄 Application Generator

This repository also includes a CLI-first application workflow under [application-system](./application-system/README.md). It is designed for job-search operations where one intake file can generate:

- a tailored cover letter
- an HTML preview
- one requested CV variant by default
- PDFs compiled from LaTeX for the cover letter and browser print for the CV
- a summary-version selection workflow for JD-specific CV positioning

Example:

```bash
python3 application-system/scripts/generate_application.py \
  --intake application-system/intakes/sample-generic-company.json \
  --compile-pdf
```

The generated CV PDF reuses the main site layout and print styles through `/generated-cv`, so the job-application engine no longer maintains a separate LaTeX CV design.

### German CV / Cover-Letter Rules

This repo now follows a stricter Germany-oriented application standard:

- the public CV must stay visually calm, easy to scan, and recruiter-safe
- the online `About` section should stay conservative and evidence-oriented
- generated CVs use stored summary variants from `application-system/data/summary_versions.json`
- the default generated summary is `strongest_balanced`
- when a JD clearly leans toward another summary style, the generator should stop and ask for a `summary_version`
- cover letters should stay one page, formal, and evidence-heavy rather than motivational fluff

The reusable rule checker lives outside the repo in the linked skill:

```bash
python3 /Users/pmlecuong/.codex/skills/job-search-cuong/scripts/check_application_rules.py \
  --resume-data src/data/resume-data.tsx \
  --summary-versions application-system/data/summary_versions.json
```

## 📁 Project Structure

```
src/
├── app/              # Next.js App Router
│   ├── layout.tsx    # Root layout with metadata
│   └── page.tsx      # Main resume page
├── components/       # React components
│   ├── ui/          # shadcn/ui components
│   └── icons/       # Icon components
├── data/            # Resume data configuration
│   └── resume-data.tsx
├── images/          # Static assets
│   └── logos/       # Company logos
└── apollo/          # GraphQL server setup
    ├── resolvers.ts
    └── type-defs.ts
```

## 🎨 Customization

### Resume Data

This CV contains my personal professional information. The resume content is stored in a single configuration file:

```typescript
// src/data/resume-data.tsx
export const RESUME_DATA = {
  name: "Cuong Le",
  initials: "CL",
  location: "Your Location",
  about: "My professional background",
  summary: "My career summary",
  // ... and more personal details
}
```

### Styling

The app uses Tailwind CSS for styling. You can customize:
- Colors in `tailwind.config.js`
- Global styles in `src/app/globals.css`
- Print styles are defined separately for optimal printing

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build the container
docker compose build

# Run the container
docker compose up -d

# Stop the container
docker compose down
```

### Using Docker directly

```bash
# Build the image
docker build -t cv-app .

# Run the container
docker run -p 3000:3000 cv-app
```

## 🔧 Configuration

### Environment Variables

No environment variables are required for basic usage. The app works out of the box!

### Print Settings

The app is optimized for printing. For best results:
- Use Chrome/Chromium for printing
- Enable "Background graphics" in print settings
- Set margins to "Default"

## 🤝 About This Project

This is my personal CV website built with modern web technologies. Feel free to:

1. Fork the repository to create your own CV
2. Use it as inspiration for your portfolio
3. Contribute improvements via Pull Requests
4. Share feedback or suggestions

If you'd like to create your own version:
- Fork this repository
- Update the resume data in `src/data/resume-data.tsx`
- Customize the styling to match your preferences
- Deploy to your preferred platform

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original template by [Bartosz Jarocki](https://github.com/BartoszJarocki/cv) - Thank you for the excellent foundation!
- [shadcn/ui](https://ui.shadcn.com/) for the beautiful UI components
- [Vercel](https://vercel.com/) for hosting and deployment platform
- The open-source community for continuous inspiration

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/nlcuong85">Cuong Le</a>
</p>
