module.exports = {
  apps: [
    {
      name: 'cv-app',
      script: 'pnpm',
      args: 'start',
      cwd: __dirname,
      instances: 1, // set to 'max' to use all CPU cores
      exec_mode: 'cluster',
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      env: {
        NODE_ENV: 'production',
        PORT: '3125',
      },
      out_file: './logs/pm2-out.log',
      error_file: './logs/pm2-error.log',
      merge_logs: true,
      time: true,
    },
  ],
};
