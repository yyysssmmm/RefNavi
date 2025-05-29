/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    turbo: {
      rules: {
        '*.pdf': {
          loaders: ['file-loader'],
          as: '*.pdf',
        },
      },
    },
  },
  webpack: (config, { isServer }) => {
    // PDF.js를 위한 설정
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        canvas: false,
        fs: false,
      };
    }

    // PDF.js worker 파일 처리
    config.module.rules.push({
      test: /pdf\.worker\.(min\.)?js/,
      type: 'asset/resource',
      generator: {
        filename: 'static/worker/[hash][ext][query]',
      },
    });

    return config;
  },
  // 정적 파일 제공 설정
  async rewrites() {
    return [
      {
        source: '/pdf-worker/:path*',
        destination: '/pdf-worker/:path*',
      },
    ];
  },
};

export default nextConfig; 