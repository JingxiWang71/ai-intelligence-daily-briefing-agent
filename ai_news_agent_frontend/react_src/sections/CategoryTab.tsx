/**
 * CategoryTab.tsx — 分类浏览 Tab
 * 按分类折叠展示新闻，可展开详细分析
 */

import { useState } from "react";
import { ChevronDown, ChevronRight, Star, ExternalLink, Lightbulb, Target, TrendingUp, TrendingDown, Minus, Eye, Compass } from "lucide-react";
import type { CategoryGroup, NewsCard as NewsCardType } from "@/types/report";

function SignalBadge({ signal }: { signal: string }) {
  const configs: Record<string, { bg: string; text: string; icon: React.ReactNode }> = {
    bullish: { bg: "bg-green-50", text: "text-green-700", icon: <TrendingUp size={12} /> },
    bearish: { bg: "bg-red-50", text: "text-red-700", icon: <TrendingDown size={12} /> },
    neutral: { bg: "bg-gray-50", text: "text-gray-600", icon: <Minus size={12} /> },
    watch:   { bg: "bg-blue-50", text: "text-blue-700", icon: <Eye size={12} /> },
  };
  const c = configs[signal] || configs.neutral;
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${c.bg} ${c.text} text-xs font-medium`}>{c.icon}{signal}</span>;
}

function TrendBadge({ trend }: { trend: string }) {
  const configs: Record<string, { bg: string; text: string; label: string }> = {
    emerging:     { bg: "bg-purple-50", text: "text-purple-700", label: "新趋势" },
    accelerating: { bg: "bg-orange-50", text: "text-orange-700", label: "加速中" },
    mature:       { bg: "bg-gray-50", text: "text-gray-600", label: "已成熟" },
    declining:    { bg: "bg-gray-100", text: "text-gray-500", label: "在衰退" },
  };
  const c = configs[trend] || configs.mature;
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${c.bg} ${c.text} text-xs font-medium`}><Compass size={12} />{c.label}</span>;
}

function ImportanceStars({ level }: { level: number }) {
  return (
    <span className="inline-flex items-center gap-0.5">
      {Array.from({ length: 5 }, (_, i) => (
        <Star key={i} size={12} className={i < level ? "text-amber-400 fill-amber-400" : "text-gray-200"} />
      ))}
    </span>
  );
}

function NewsCard({ card }: { card: NewsCardType }) {
  const [expanded, setExpanded] = useState(false);
  const summary = card.summary;

  return (
    <div className="border border-gray-100 rounded-lg hover:shadow-md transition-shadow duration-200 bg-white">
      <div className="p-4">
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <ImportanceStars level={card.importance} />
          {summary && <SignalBadge signal={summary.investment_signal} />}
          {summary && <TrendBadge trend={summary.tech_trend} />}
          <span className="text-xs text-gray-400 ml-auto">{card.source}</span>
        </div>

        <h3 className="text-sm font-semibold text-gray-900 mb-2 leading-snug">{card.title}</h3>

        {card.compressed_article && (
          <div className="text-xs text-gray-500 mb-3 whitespace-pre-line bg-gray-50 rounded p-2.5">{card.compressed_article}</div>
        )}

        <p className="text-xs text-gray-400 mb-3"><Target size={10} className="inline mr-1" />{card.reason}</p>

        {summary && (
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 mb-3">
            <div className="flex items-center gap-1.5 mb-1">
              <Lightbulb size={13} className="text-blue-600" />
              <span className="text-xs font-semibold text-blue-700">核心观点</span>
            </div>
            <p className="text-xs text-blue-800 leading-relaxed">{summary.key_takeaway}</p>
          </div>
        )}

        <div className="flex items-center justify-between">
          {summary && (
            <button onClick={() => setExpanded(!expanded)} className="text-xs text-gray-400 hover:text-blue-600 transition-colors flex items-center gap-1">
              {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              {expanded ? "收起分析" : "展开详细分析"}
            </button>
          )}
          <a href={card.link} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-500 hover:text-blue-700 flex items-center gap-1 transition-colors ml-auto">
            <ExternalLink size={12} />阅读原文
          </a>
        </div>
      </div>

      {expanded && summary && (
        <div className="border-t border-gray-100 px-4 pb-4 pt-3 space-y-3">
          <div>
            <p className="text-xs font-semibold text-gray-700 mb-1.5">行业影响</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div className="bg-amber-50 rounded p-2.5">
                <p className="text-[10px] text-amber-600 font-medium mb-0.5">短期（1-3个月）</p>
                <p className="text-xs text-amber-800">{summary.industry_impact.short_term}</p>
              </div>
              <div className="bg-indigo-50 rounded p-2.5">
                <p className="text-[10px] text-indigo-600 font-medium mb-0.5">长期（6-12个月）</p>
                <p className="text-xs text-indigo-800">{summary.industry_impact.long_term}</p>
              </div>
            </div>
          </div>

          {summary.competitive_landscape && (
            <div>
              <p className="text-xs font-semibold text-gray-700 mb-1">竞争格局变化</p>
              <p className="text-xs text-gray-600 leading-relaxed">{summary.competitive_landscape}</p>
            </div>
          )}

          {summary.actionable_insights.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-700 mb-1.5">行动建议</p>
              <ul className="space-y-1">
                {summary.actionable_insights.map((insight, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-xs text-gray-600">
                    <span className="flex-shrink-0 w-4 h-4 rounded-full bg-green-50 text-green-600 flex items-center justify-center text-[10px] font-bold mt-0.5">{idx + 1}</span>
                    {insight}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function CategoryGroupPanel({ group }: { group: CategoryGroup }) {
  const [isOpen, setIsOpen] = useState(true);
  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <button onClick={() => setIsOpen(!isOpen)} className="w-full flex items-center justify-between px-5 py-4 bg-gray-50 hover:bg-gray-100 transition-colors text-left">
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-gray-800">{group.category}</span>
          <span className="px-2 py-0.5 rounded-full bg-white text-gray-500 text-xs font-medium border border-gray-200">{group.count}</span>
        </div>
        {isOpen ? <ChevronDown size={18} className="text-gray-400" /> : <ChevronRight size={18} className="text-gray-400" />}
      </button>
      {isOpen && (
        <div className="p-4 space-y-3 bg-white">
          {group.news.map((card) => <NewsCard key={card.id} card={card} />)}
        </div>
      )}
    </div>
  );
}

export function CategoryTab({ groups }: { groups: CategoryGroup[] }) {
  return <div className="space-y-4">{groups.map((g) => <CategoryGroupPanel key={g.category} group={g} />)}</div>;
}