/**
 * DailyDigest.tsx — 每日摘要
 */

import { Newspaper, TrendingUp, TrendingDown, Minus, Eye } from "lucide-react";
import type { DailyDigest } from "@/types/report";

function SentimentIcon({ sentiment }: { sentiment: string }) {
  const s = sentiment.toLowerCase();
  if (s === "bullish") return <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-green-100 text-green-700 text-sm font-medium"><TrendingUp size={14} />利好</span>;
  if (s === "bearish") return <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-red-100 text-red-700 text-sm font-medium"><TrendingDown size={14} />利空</span>;
  if (s === "neutral") return <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-gray-100 text-gray-600 text-sm font-medium"><Minus size={14} />中性</span>;
  return <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm font-medium"><Eye size={14} />观望</span>;
}

export function DailyDigestSection({ digest }: { digest: DailyDigest }) {
  return (
    <section className="mb-6">
      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Newspaper size={20} className="text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">每日摘要</h2>
          </div>
          <SentimentIcon sentiment={digest.market_sentiment} />
        </div>
        <p className="text-base text-gray-800 leading-relaxed mb-4">{digest.headline}</p>
        {digest.top_stories.length > 0 && (
          <div className="border-t border-gray-100 pt-4">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">TOP 3 新闻</p>
            <ol className="space-y-2">
              {digest.top_stories.slice(0, 3).map((story, i) => (
                <li key={i} className="flex items-start gap-3 text-sm text-gray-600">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center text-xs font-bold mt-0.5">{i + 1}</span>
                  <span className="line-clamp-2">{story}</span>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </section>
  );
}