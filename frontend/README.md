# Download Manager Frontend

React and Vite frontend for the download API.

## Run locally

Install Node.js, then from this directory:

```sh
npm install
npm run dev
```

The Vite development server proxies `/downloads` to `http://127.0.0.1:8000` by default. Start the API separately, or set `API_PROXY_TARGET` to its base URL before starting Vite.

The app provides an add-download form for a direct URL, magnet link, or info hash, plus a status page that lists downloads from `GET /downloads`.