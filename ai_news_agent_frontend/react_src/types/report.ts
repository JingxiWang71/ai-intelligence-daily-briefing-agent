/**
 * report.ts — 数据类型定义
 *
 * 描述 report.json 的数据结构。
 * 如果后端改了数据格式，改这里即可。
 */

export interface ReportMeta {
  generated_at: string;
  total_news: number;
  ai_news_count: number;
  date_range: { start: string; end: string };
}

export interface ReportOverview {
  category_distribution: Record<string, number>;
  importance_distribution: Record<string, number>;
  signal_distribution: Record<string, number>;
  trend_distribution: Record<string, number>;
  top_keywords: string[];
}

export interface DailyDigest {
  headline: string;
  top_stories: string[];
  market_sentiment: string;
}

export interface NewsSummary {
  key_takeaway: string;
  industry_impact: { short_term: string; long_term: string };
  investment_signal: "bullish" | "bearish" | "neutral" | "watch";
  tech_trend: "emerging" | "accelerating" | "mature" | "declining";
  competitive_landscape: string;
  actionable_insights: string[];
}

export interface NewsCard {
  id: number;
  title: string;
  source: string;
  link: string;
  published: string;
  importance: number;
  category: string;
  compressed_article: string;
  reason: string;
  summary: NewsSummary | null;
}

export interface CategoryGroup {
  category: string;
  count: number;
  news: NewsCard[];
}

export interface FeaturedNews {
  id: number;
  title: string;
  source: string;
  link: string;
  importance: number;
  category: string;
  key_takeaway: string;
  investment_signal: string;
}

export interface SignalGroup {
  signal: string;
  label: string;
  count: number;
  news: FeaturedNews[];
}

export interface Report {
  meta: ReportMeta;
  overview: ReportOverview;
  daily_digest: DailyDigest;
  categories: CategoryGroup[];
  featured: FeaturedNews[];
  investment_signals: SignalGroup[];
}