/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Static export: the whole site is HTML and JSON on a CDN. There is no server
  // to keep warm, nothing to expire, and no way for the pages to disagree with
  // the notebooks -- they are generated from the same committed data.
  output: "export",
  images: { unoptimized: true },
  trailingSlash: true,
};

export default nextConfig;
