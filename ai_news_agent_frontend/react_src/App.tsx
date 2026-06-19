/**
 * App.tsx — 前端主组件
 *
 * 组装所有区域：头部 → 概览 → 摘要 → Tab导航 → Tab内容 → 页脚
 */

import { useState } from "react";
import { LayoutGrid, Star, TrendingUp, BarChart3, RefreshCw, Bot, Newspaper } from "lucide-react";
import { useReport } from "@/hooks/useReport";
import { OverviewPanel } from "@/sections/OverviewPanel";
import { DailyDigestSection } from "@/sections/DailyDigest";
import { CategoryTab } from "@/sections/CategoryTab";
import { FeaturedTab } from "@/sections/FeaturedTab";
import { SignalTab } from "@/sections/SignalTab";
import { TrendTab } from "@/sections/TrendTab";

const TABS = [
  { id: "categories", label: "分类浏览", icon: <LayoutGrid size={16} /> },
  { id: "featured", label: "重要精选", icon: <Star size={16} /> },
  { id: "signals", label: "投资信号", icon: <TrendingUp size={16} /> },
  { id: "trends", label: "趋势追踪", icon: <BarChart3 size={16} /> },
];

function LoadingSkeleton() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8 animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-48 mb-8" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[...Array(4)].map((_, i) => <div key={i} className="h-24 bg-gray-100 rounded-xl" />)}
      </div>
      <div className="h-32 bg-gray-100 rounded-xl mb-6" />
      <div className="h-9 bg-gray-100 rounded-lg w-full mb-6" />
    </div>
  );
}

function ErrorDisplay({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="max-w-5xl mx-auto px-4 py-16 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-50 mb-4">
        <Newspaper size={28} className="text-red-400" />
      </div>
      <h2 className="text-lg font-semibold text-gray-800 mb-2">加载失败</h2>
      <p className="text-sm text-gray-500 mb-6">{message}</p>
      <button onClick={onRetry} className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">重新加载</button>
    </div>
  );
}

export default function App() {
  const { report, loading, error, refetch } = useReport();
  const [activeTab, setActiveTab] = useState("categories");

  if (loading) return <LoadingSkeleton />;
  if (error || !report) return <ErrorDisplay message={error || "数据为空"} onRetry={refetch} />;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 头部 */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center">
              <Bot size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">AI 产业日报</h1>
              <p className="text-xs text-gray-400">{report.meta.ai_news_count} 条 AI 新闻 · {new Date(report.meta.generated_at).toLocaleDateString("zh-CN")}</p>
            </div>
          </div>
          <button onClick={refetch} className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
            <RefreshCw size={15} /><span className="hidden sm:inline">刷新</span>
          </button>
        </div>
      </header>

      {/* 主内容 */}
      <main className="max-w-5xl mx-auto px-4 py-6">
        <OverviewPanel overview={report.overview} />
        <DailyDigestSection digest={report.daily_digest} />

        {/* Tab 导航 */}
        <nav className="flex gap-1 p-1 bg-gray-100 rounded-xl mb-6">
          {TABS.map((tab) => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id ? "bg-white text-blue-700 shadow-sm" : "text-gray-500 hover:text-gray-700"
              }`}>
              {tab.icon}<span className="hidden sm:inline">{tab.label}</span>
            </button>
          ))}
        </nav>

        {/* Tab 内容 */}
        <div className="pb-12">
          {activeTab === "categories" && <CategoryTab groups={report.categories} />}
          {activeTab === "featured" && <FeaturedTab news={report.featured} />}
          {activeTab === "signals" && <SignalTab signals={report.investment_signals} />}
          {activeTab === "trends" && <TrendTab overview={report.overview} />}
        </div>
      </main>

      {/* 页脚 */}
      <footer className="border-t border-gray-200 bg-white">
        <div className="max-w-5xl mx-auto px-4 py-4 text-xs text-gray-400 text-center">
          AI 产业新闻 Agent · 自动生成
        </div>
      </footer>
    </div>
  );
}