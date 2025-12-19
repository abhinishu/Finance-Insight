# Finance-Insight Frontend

React TypeScript application for Finance-Insight Discovery Screen.

## Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

## Features

- **Discovery Screen**: Select Atlas Structure and view hierarchy with natural values
- **AG-Grid Tree View**: Expandable hierarchy display
- **Natural Values**: Daily, MTD, YTD P&L measures automatically populated

## Environment Variables

Create `.env` file:
```
VITE_API_BASE_URL=http://localhost:8000
```

## Development

The frontend runs on `http://localhost:3000` and proxies API requests to `http://localhost:8000`.

