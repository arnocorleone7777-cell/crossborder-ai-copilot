import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],build:{rollupOptions:{output:{manualChunks:{charts:['echarts/core','echarts/charts','echarts/components','echarts/renderers'],react:['react','react-dom']}}}},server:{proxy:{'/api':'http://127.0.0.1:8000','/assets/generated':'http://127.0.0.1:8000'}}});
