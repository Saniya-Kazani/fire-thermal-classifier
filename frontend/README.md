# Fire Thermal Classifier Frontend

## Run locally

```sh
npm install
npm run dev
```

Set the public FastAPI service origin in `.env.local`:

```env
VITE_API_BASE_URL=https://fire-thermal-classifier.onrender.com
```

The dashboard reads `/api/hotspots`, `/api/alerts`, and the selected hotspot's
`/api/hotspots/{id}/history` endpoint. When the backend is unavailable, it
shows demo data with a visible warning.

## Vercel

Set `VITE_API_BASE_URL` to `https://fire-thermal-classifier.onrender.com` in the
Vercel project's Environment Variables, then redeploy. Never put a database URL
or password in a `VITE_` variable; Vite exposes those values in browser code.