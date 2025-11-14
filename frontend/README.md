# AI Social Media Manager - Frontend

Next.js 14 frontend application for the AI Social Media Manager.

## Structure

```
frontend/
├── app/              # Next.js 14 App Router
│   ├── layout.tsx    # Root layout
│   ├── page.tsx      # Homepage
│   ├── upload/       # Upload page
│   ├── schedule/     # Schedule page
│   └── analytics/    # Analytics page
├── public/          # Static assets
├── __tests__/       # Unit tests
├── e2e/            # E2E tests
├── package.json    # Dependencies
├── next.config.js  # Next.js configuration
└── tsconfig.json   # TypeScript configuration
```

## Features

- ✅ Next.js 14 with App Router
- ✅ TypeScript support
- ✅ Backend health check
- ✅ Responsive design
- ✅ API integration ready
- ✅ Standalone build output for Docker

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run tests
npm test

# Run E2E tests
npm run test:e2e
```

## Environment Variables

- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL (default: http://localhost:8000)
- `PORT` - Server port (set by Render automatically)

## Deployment

The frontend is configured for deployment on Render with:
- Standalone output for minimal Docker image
- Automatic PORT handling
- Production optimizations

See `../infra/RENDER_DEPLOY.md` for deployment instructions.

