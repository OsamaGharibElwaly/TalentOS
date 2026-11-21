import type { NextConfig } from 'next';

// CSP is set per request in src/proxy.ts with a nonce; a static header here
// would be enforced alongside it and block Next.js inline bootstrap scripts.
const securityHeaders = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=(), payment=()',
  },
];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async rewrites() {
    const targets = ['frontend', 'jobs', 'applications', 'interviews', 'search', 'api'];
    return [
      // /jobs is also a page, so afterFiles rewrites would serve HTML to the API client.
      {
        source: '/frontend/jobs/:path*',
        destination: 'http://127.0.0.1:8000/jobs/:path*',
      },
      ...targets.map((target) => ({
        source: `/${target}/:path*`,
        destination: `http://127.0.0.1:8000/${target}/:path*`,
      })),
    ];
  },
  async headers() {
    return [
      { source: '/:path*', headers: securityHeaders },
      {
        source: '/api/:path*',
        headers: [{ key: 'Cache-Control', value: 'no-store' }],
      },
      {
        source: '/frontend/:path*',
        headers: [{ key: 'Cache-Control', value: 'no-store' }],
      },
    ];
  },
};

export default nextConfig;
