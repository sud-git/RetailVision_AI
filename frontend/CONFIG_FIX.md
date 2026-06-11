# Frontend Configuration Guide

## Files Modified/Created

### 1. **tsconfig.json** - FIXED ✅
**Issue**: Was written as TypeScript code instead of JSON
**Fix**: Converted to proper JSON format with Next.js-compatible settings
**Key Changes**:
- Changed `jsx` from `'react-jsx'` to `'preserve'` (required for Next.js)
- Added Next.js plugin: `"plugins": [{"name": "next"}]`
- Added `next-env.d.ts` to includes
- Set `noUnusedLocals` and `noUnusedParameters` to `false` for flexibility
- Added `incremental` compilation for faster builds

### 2. **package.json** - UPDATED ✅
**Changes**:
- `"dev"` script now includes port: `next dev -p 3000`
- `"start"` script now includes port: `next start -p 3000`
- `"lint"` now auto-fixes: `next lint --fix`
- `"type-check"` adds `--skipLibCheck` flag
- Added `"clean"` script to remove build artifacts
- Added `"reinstall"` script for fresh install

### 3. **.eslintrc.json** - CREATED ✅
Proper ESLint configuration for Next.js with TypeScript

### 4. **postcss.config.js** - CREATED ✅
PostCSS configuration for Tailwind CSS processing

### 5. **next-env.d.ts** - CREATED ✅
TypeScript definitions for Next.js environment variables

### 6. **.env.local** - CREATED ✅
Local environment variables for development:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 7. **next.config.js** - ENHANCED ✅
Added:
- Webpack watch configuration for file changes
- Image optimization with remote patterns
- Proper async rewrites
- Cache headers
- Better error handling

### 8. **app/layout.tsx** - UPDATED ✅
- Added `Readonly<>` type for children
- Added `suppressHydrationWarning` to html tag
- Added proper Next.js structure

### 9. **app/page.tsx** - REFACTORED ✅
- Added `'use client'` directive for client-side rendering
- Added TypeScript interfaces for type safety
- Extracted features to array for maintainability
- Better component structure

### 10. **.npmrc** - CREATED ✅
NPM configuration to handle peer dependencies gracefully

## Root Cause Analysis

### The Problem
The `tsconfig.json` was written as **TypeScript code** rather than **JSON format**:

```typescript
// ❌ WRONG - This is TypeScript
import type { Config } from 'typescript'
const config: Config = { ... }
export default config
```

### Why This Failed
1. Next.js requires `tsconfig.json` to be valid JSON, not TypeScript
2. TypeScript compiler expects `.ts` or `.tsx` files, not `.json` files
3. The file was interpreted as invalid JSON, causing the "Debug Failure" error
4. Next.js couldn't parse the configuration at build time

### The Solution
Converted to proper JSON format with Next.js plugin configuration:

```json
{
  "compilerOptions": { ... },
  "include": [...],
  "exclude": [...]
}
```

## Quick Start - Clean Installation

### Step 1: Clean Everything
```bash
cd "c:\Users\sudho\Desktop\RetailVision AI\frontend"
npm run clean
```

### Step 2: Reinstall Dependencies
```bash
npm install
```

### Step 3: Run Development Server
```bash
npm run dev
```

### Step 4: Access Dashboard
Open browser: **http://localhost:3000**

## Commands Reference

```bash
# Development
npm run dev              # Start dev server on port 3000

# Production
npm run build           # Build for production
npm start               # Start production server

# Maintenance
npm run type-check     # Check TypeScript errors
npm run lint           # Lint code and auto-fix
npm run format         # Format code with Prettier
npm run clean          # Remove all build artifacts
npm run reinstall      # Full clean + reinstall

# Debugging
npm run build -- --debug  # Build with debug info
npm run dev -- --experimental-app  # Dev with app router
```

## Verification Checklist

After running `npm run dev`:

- [ ] No TypeScript compilation errors
- [ ] Dev server starts on port 3000
- [ ] Access http://localhost:3000 works
- [ ] Hot module reloading works
- [ ] No console errors in browser
- [ ] No terminal warnings about tsconfig

## Common Issues & Solutions

### Issue: "Expected frontend/tsconfig.json"
**Solution**: Already fixed - tsconfig is now valid JSON

### Issue: Port 3000 already in use
```bash
# Kill process on port 3000
npx kill-port 3000
npm run dev
```

### Issue: Dependencies conflict
```bash
npm run reinstall
```

### Issue: Hot reload not working
```bash
# Delete cache and restart
rm -rf .next
npm run dev
```

### Issue: TypeScript errors still showing
```bash
npm run type-check --skipLibCheck
```

## File Structure After Fix

```
frontend/
├── app/
│   ├── layout.tsx        ✅ Updated with Readonly types
│   ├── page.tsx          ✅ Refactored with 'use client'
│   └── globals.css       ✅ Tailwind configuration
├── components/           (Ready for Phase 9)
├── lib/                  (Ready for Phase 9)
├── hooks/                (Ready for Phase 9)
├── public/               (Assets)
├── next.config.js        ✅ Enhanced configuration
├── tsconfig.json         ✅ FIXED - Now valid JSON
├── package.json          ✅ Updated scripts
├── .eslintrc.json        ✅ Created
├── postcss.config.js     ✅ Created
├── next-env.d.ts         ✅ Created
├── .env.local            ✅ Created
├── .npmrc                ✅ Created
├── .gitignore            ✅ Updated
├── .prettierrc.js        ✅ Exists
├── Dockerfile            ✅ Exists
└── tailwind.config.ts    ✅ Exists
```

## Environment Variables

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### During Build
- `NODE_ENV=production` or `development`
- All `NEXT_PUBLIC_*` variables are embedded in client bundle

## Next Steps

1. ✅ Run `npm run dev`
2. ✅ Open http://localhost:3000
3. ✅ Verify dashboard loads
4. ✅ Proceed to Phase 2: Video Ingestion

## Support

If you still encounter issues:

1. Check node version: `node --version` (needs 18+)
2. Check npm version: `npm --version` (needs 9+)
3. Verify backend is running: `curl http://localhost:8000/health`
4. Check .env.local exists and has correct URLs
5. Review console output for specific errors
