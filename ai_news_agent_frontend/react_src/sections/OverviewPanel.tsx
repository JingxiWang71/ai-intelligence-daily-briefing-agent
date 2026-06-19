/**
 * OverviewPanel.tsx — 4 张统计卡片
 */

import { BarChart3, Flame, TrendingUp, Zap } from "lucide-react";
import type { ReportOverview } from "@/types/report";

function StatCard({ title, value, subtitle, icon, bgColor, textColor }: {
  title: string; value: string | number; subtitle: string;
  icon: React.ReactNode; bgColor: string; textColor: string;
}) {
  return (
    <div className={`${bgColor} rounded-xl p-5 flex items-start gap-4`}>
      <div className={`${textColor} mt-1`}>{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-500 font-medium">{title}</p>
        <p className={`text-2xl font-bold ${textColor} mt-1`}>{value}</p>
        <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
      </div>
    </div>
  );
}

export function OverviewPanel({ overview }: { overview: ReportOverview }) {
  const majorEvents = overview.importance_distribution["5"] || 0;
  const bullishCount = overview.signal_distribution["bullish"] || 0;
  const acceleratingCount = overview.trend_distribution["accelerating"] || 0;
  const totalAI = Object.values(overview.category_distribution).reduce((s, c) => s + c, 0);

  return (
    <section className="mb-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="今日 AI 新闻" value={totalAI} subtitle="条相关报道"
          icon={<BarChart3 size={24} />} bgColor="bg-blue-50" textColor="text-blue-700" />
        <StatCard title="重大事件" value={majorEvents} subtitle="5星重要性新闻"
          icon={<Flame size={24} />} bgColor="bg-red-50" textColor="text-red-600" />
        <StatCard title="利好信号" value={`+${bullishCount}`} subtitle="bullish 信号"
          icon={<TrendingUp size={24} />} bgColor="bg-green-50" textColor="text-green-600" />
        <StatCard title="加速趋势" value={acceleratingCount} subtitle="项技术正在加速"
          icon={<Zap size={24} />} bgColor="bg-amber-50" textColor="text-amber-600" />
      </div>
    </section>
  );
}