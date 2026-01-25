import {defineConfig} from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
    plugins: [
        react(),
        tailwindcss(),
    ],
    base: '/discord/web', // 設置基礎路徑
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
            '@/features': path.resolve(__dirname, './src/features'),
            '@/shared': path.resolve(__dirname, './src/shared'),
            '@/core': path.resolve(__dirname, './src/core'),
        },
    },
    build: {
        outDir: '../static/dist', // 改成你的實際 addon 路徑
        emptyOutDir: true,
    },
})
