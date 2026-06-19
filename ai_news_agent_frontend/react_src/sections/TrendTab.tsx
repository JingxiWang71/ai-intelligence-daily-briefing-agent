/**
 * TrendTab.tsx — 趋势追踪 Tab
 * 技术趋势分布 + 关键词云 + 分类分布
 */

import { Rocket, Zap, CheckCircle2, TrendingDown, Tag, BarChart3 } from "lucide-react";
import type { ReportOverview } from "@/types/report";

const TREND_CONFIGS: Record<string, { label: string; icon: React.ReactNode; color: string; bg: string }> = {
  emerging:     { label: "新趋势萌芽", icon: <Rocket size={18} />, color: "text-purple-700", bg: "bg-purple-50" },
  accelerating: { label: "正在加速", icon: <Zap size={18} />, color: "text-orange-700", bg: "bg-orange-50" },
  mature:       { label: "趋于成熟", icon: <CheckCircle2 size={18} />, color: "text-gray-700", bg: "bg-gray-50" },
  declining:    { label: "走向衰落", icon: <TrendingDown size={18} />, color: "text-gray-500", bg: "bg-gray-100" },
};

function TrendDistribution({ trends }: { trends: Record<string, number> }) {
  const total = Object.values(trends).reduce((s, v) => s + v, 0);
  if (total === 0) return null;
  return (
    <div className="space-y-3">
      {["emerging", "accelerating", "mature", "declining"].map((key) => {
        const count = trends[key] || 0;
        const config = TREND_CONFIGS[key];
        const percentage = Math.round((count / total) * 100);
        return (
          <div key={key} className="flex items-center gap-4">
            <div className={`flex items-center gap-2 w-28 flex-shrink-0 ${config.color}`}>
              {config.icon}
              <span className="text-sm font-medium">{config.label}</span>
            </div>
            <div className="flex-1 h-8 bg-gray-100 rounded-lg overflow-hidden relative">
              <div className={`h-full ${config.bg} transition-all duration-500 flex items-center`} style={{ width: `${percentage}%` }}>
                {percentage > 15 && <span className={`text-xs font-bold ml-3 ${config.color}`}>{count} 条</span>}
              </div>
              {percentage <= 15 && <span className="absolute inset-y-0 left-2 flex items-center text-xs text-gray-500">{count} 条 ({percentage}%)</span>}
            </div>
            <span className="text-xs text-gray-400 w-12 text-right">{percentage}%</span>
          </div>
        );
      })}
    </div>
  );
}

function KeywordCloud({ keywords }: { keywords: string[] }) {
  if (keywords.length === 0) return null;
  const colorClasses = [
    "text-blue-600 bg-blue-50", "text-green-600 bg-green-50", "text-purple-600 bg-purple-50",
    "text-orange-600 bg-orange-50", "text-red-600 bg-red-50", "text-indigo-600 bg-indigo-50",
    "text-teal-600 bg-teal-50", "text-pink-600 bg-pink-50", "text-amber-600 bg-amber-50", "text-cyan-600 bg-cyan-50",
  ];
  const sizeClasses = ["text-lg font-bold", "text-base font-semibold", "text-sm font-medium", "text-xs font-normal"];
  return (
    <div className="flex flex-wrap gap-2">
      {keywords.map((word, index) => (
        <span key={word} className={`inline-flex items-center px-3 py-1.5 rounded-full ${colorClasses[index % colorClasses.length]} ${sizeClasses[index % sizeClasses.length]}`}>
          <Tag size={12} className="mr-1.5 opacity-50" />{word}
        </span>
      ))}
    </div>
  );
}

export function TrendTab({ overview }: { overview: ReportOverview }) {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-5">
          <BarChart3 size={18} className="text-purple-600" />
          <h3 className="text-base font-semibold text-gray-900">技术趋势分布</h3>
        </div>
        <TrendDistribution trends={overview.trend_distribution} />
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-5">
          <Tag size={18} className="text-blue-600" />
          <h3 className="text-base font-semibold text-gray-900">今日关键词</h3>
          <span className="text-xs text-gray-400 ml-2">基于新闻标题提取的高频词汇</span>
        </div>
        <KeywordCloud keywords={overview.top_keywords} />
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-5">
          <Zap size={18} className="text-orange-600" />
          <h3 className="text-base font-semibold text-gray-900">分类分布</h3>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {Object.entries(overview.category_distribution).map(([category, count]) => (
            <div key={category} className="flex items-center justify-between px-4 py-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-700">{category}</span>
              <span className="text-sm font-bold text-gray-900">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}