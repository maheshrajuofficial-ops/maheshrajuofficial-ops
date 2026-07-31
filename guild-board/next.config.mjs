/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      // Supabase Storage buckets (identity docs, task photos, completion proof).
      { protocol: 'https', hostname: '*.supabase.co', pathname: '/storage/v1/object/public/**' },
      { protocol: 'https', hostname: 'api.mapbox.com' },
    ],
  },
  experimental: {
    // Stripe's SDK is CJS and pulls in Node built-ins; keep it out of the bundler graph.
    serverComponentsExternalPackages: ['stripe'],
  },
};

export default nextConfig;
