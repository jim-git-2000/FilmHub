/** @type {import('next').NextConfig} */
const config = {
  output: 'standalone',
  poweredByHeader: false,
  async rewrites() {
    const origin = process.env.API_ORIGIN || 'http://127.0.0.1:8000';
    return [{source: '/api/:path*', destination: `${origin}/api/:path*`}, {source: '/uploads/:path*', destination: `${origin}/uploads/:path*`}];
  },
  async headers() {
    return [{source: '/:path*', headers: [{key: 'X-Content-Type-Options', value: 'nosniff'}, {key: 'Referrer-Policy', value: 'same-origin'}, {key: 'X-Frame-Options', value: 'DENY'}]}];
  },
};
export default config;
