/**
 * SignalTab.tsx — 投资信号 Tab
 */

import { useState } from "react";
import { TrendingUp, TrendingDown, Eye, Minus, Star, ExternalLink, ChevronDown, ChevronRight } from "lucide-react";
import type { SignalGroup, FeaturedNews } from "@/types/report";

function getSignalConfig(signal: string) {
  const configs: Record<string, { icon: React.ReactNode; color: string; bg: string; border: string; desc: string }> = {
    bullish: { icon: <TrendingUp size={20} />, color: "text-green-700", bg: "bg-green-50", border: "border-green-200", desc: "对相关赛道或公司构成利好" },
    bearish: { icon: <TrendingDown size={20} />, color: "text-red-700", bg: "bg-red-50", border: "border-red-200", desc: "对相关赛道或公司构成利空" },
    watch:   { icon: <Eye size={20} />, color: "text-blue-700", bg: "bg-blue-50", border: "border-blue-200", desc: "值得密切关注后续发展" },
    neutral: { icon: <Minus size={20} />, color: "text-gray-600", bg: "bg-gray-50", border: "border-gray-200", desc: "影响偏中性" },
  };
  return configs[signal] || configs.neutral;
}

function SignalNewsCard({ news, signalColor }: { news: FeaturedNews; signalColor: string }) {
  return (
    <div className="border border-gray-100 rounded-lg p-3.5 hover:shadow-sm transition-shadow bg-white">
      <div className="flex items-start justify-between gap-3 mb-1.5">
        <h4 className="text-sm font-medium text-gray-900 leading-snug flex-1">{news.title}</h4>
        <span className="text-xs text-gray-400 flex-shrink-0">{news.source}</span>
      </div>
      {news.key_takeaway && <p className="text-xs text-gray-500 leading-relaxed mb-2">{news.key_takeaway}</p>}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-0.5 text-xs">
            {Array.from({ length: 5 }, (_, i) => (
              <Star key={i} size={10} className={i < news.importance ? "text-amber-400 fill-amber-400" : "text-gray-200"} />
            ))}
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">{news.category}</span>
        </div>
        <a href={news.link} target="_blank" rel="noopener noreferrer" className={`text-xs flex items-center gap-1 transition-colors ${signalColor} hover:opacity-70`}><ExternalLink size={11} />原文</a>
      </div>
    </div>
  );
}

function SignalGroupPanel({ group }: { group: SignalGroup }) {
  const config = getSignalConfig(group.signal);
  const [isOpen, setIsOpen] = useState(true);
  return (
    <div className={`border rounded-xl overflow-hidden ${config.border}`}>
      <button onClick={() => setIsOpen(!isOpen)} className={`w-full flex items-center justify-between px-5 py-4 ${config.bg} hover:opacity-80 transition-opacity text-left`}>
        <div className="flex items-center gap-3">
          <span className={config.color}>{config.icon}</span>
          <div>
            <span className={`text-sm font-bold ${config.color}`}>{group.label}</span>
            <span className="ml-2 text-xs text-gray-400">{config.desc}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${config.bg} ${config.color} border ${config.border}`}>{group.count} 条</span>
          {isOpen ? <ChevronDown size={18} className="text-gray-400" /> : <ChevronRight size={18} className="text-gray-400" />}
        </div>
      </button>
      {isOpen && (
        <div className="p-4 space-y-3 bg-white">
          {group.news.map((item) => <SignalNewsCard key={item.id} news={item} signalColor={config.color} />)}
        </div>
      )}
    </div>
  );
}

export function SignalTab({ signals }: { signals: SignalGroup[] }) {
  if (signals.length === 0) return <div className="text-center py-16 text-gray-400"><TrendingUp size={48} className="mx-auto mb-4 opacity-30" /><p className="text-sm">暂无投资信号数据</p></div>;
  const order = ["bullish", "watch", "bearish", "neutral"];
  const sorted = [...signals].sort((a, b) => order.indexOf(a.signal) - order.indexOf(b.signal));
  return (
    <div className="space-y-4">
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-xs text-gray-500">投资信号基于新闻对 AI 产业链的潜在影响进行判断，仅供参考不构成投资建议。<span className="text-blue-500 font-medium ml-1">共 {signals.reduce((s, g) => s + g.count, 0)} 条信号</span></p>
      </div>
      {sorted.map((group) => <SignalGroupPanel key={group.signal} group={group} />)}
    </div>
  );
}