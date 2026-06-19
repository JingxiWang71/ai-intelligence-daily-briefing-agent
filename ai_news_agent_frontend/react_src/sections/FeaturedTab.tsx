/**
 * FeaturedTab.tsx — 重要精选 Tab
 */

import { Star, ExternalLink, TrendingUp, TrendingDown, Eye, Minus } from "lucide-react";
import type { FeaturedNews } from "@/types/report";

function getSignalConfig(signal: string) {
  const configs: Record<string, { border: string; bg: string; badge: string }> = {
    bullish: { border: "border-l-green-400", bg: "bg-green-50/50", badge: "bg-green-100 text-green-700" },
    bearish: { border: "border-l-red-400", bg: "bg-red-50/50", badge: "bg-red-100 text-red-700" },
    watch:   { border: "border-l-blue-400", bg: "bg-blue-50/50", badge: "bg-blue-100 text-blue-700" },
    neutral: { border: "border-l-gray-300", bg: "bg-gray-50/50", badge: "bg-gray-100 text-gray-600" },
  };
  return configs[signal] || configs.neutral;
}

function FeaturedCard({ item, index }: { item: FeaturedNews; index: number }) {
  const config = getSignalConfig(item.investment_signal);
  return (
    <div className={`border border-gray-100 rounded-xl ${config.bg} hover:shadow-md transition-all overflow-hidden`}>
      <div className={`flex border-l-4 ${config.border}`}>
        <div className="flex-1 p-4">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className="w-6 h-6 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center text-xs font-bold">{index + 1}</span>
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold ${item.importance >= 4 ? "bg-red-100 text-red-700" : "bg-yellow-100 text-yellow-700"}`}>
              <Star size={10} className="fill-current" />{item.importance}星
            </span>
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${config.badge}`}>
              {item.investment_signal === "bullish" && <TrendingUp size={12} />}
              {item.investment_signal === "bearish" && <TrendingDown size={12} />}
              {item.investment_signal === "watch" && <Eye size={12} />}
              {item.investment_signal === "neutral" && <Minus size={12} />}
              {item.investment_signal}
            </span>
            <span className="text-xs text-gray-400 ml-auto">{item.source}</span>
          </div>
          <h3 className="text-sm font-semibold text-gray-900 mb-2 leading-snug">{item.title}</h3>
          {item.key_takeaway && <p className="text-xs text-gray-600 leading-relaxed mb-3">{item.key_takeaway}</p>}
          <div className="flex items-center justify-between">
            <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-500">{item.category}</span>
            <a href={item.link} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-500 hover:text-blue-700 flex items-center gap-1"><ExternalLink size={11} />阅读原文</a>
          </div>
        </div>
      </div>
    </div>
  );
}

export function FeaturedTab({ news }: { news: FeaturedNews[] }) {
  if (news.length === 0) return <div className="text-center py-16 text-gray-400"><Star size={48} className="mx-auto mb-4 opacity-30" /><p className="text-sm">暂无重要新闻</p></div>;
  return (
    <div className="space-y-3">
      <p className="text-xs text-gray-400">按重要性排序，共 {news.length} 条</p>
      {news.map((item, index) => <FeaturedCard key={item.id} item={item} index={index} />)}
    </div>
  );
}