/**
 * main.tsx — React 程序入口
 *
 * 作用：把 App 组件渲染到 index.html 中的 <div id="root"> 里
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// createRoot 创建一个 React 根节点，绑定到 DOM 中的 <div id="root">
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)