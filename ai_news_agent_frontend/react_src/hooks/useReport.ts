/**
 * useReport.ts — 读取报告数据
 *
 * 直接用 import 加载 JSON，绕过 fetch 的网络请求。
 * 比 fetch 更可靠，不需要担心路径问题。
 */

import { useState, useEffect } from "react";
import type { Report } from "@/types/report";

// Vite 内置支持直接 import JSON 文件
import reportData from "@/data/report.json";

export function useReport() {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = () => {
    setLoading(true);
    setError(null);

    try {
      // 直接赋值，不需要 fetch
      setReport(reportData as unknown as Report);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "未知错误";
      setError(`加载报告失败: ${msg}`);
      console.error("[useReport] 加载数据失败:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return {
    report,
    loading,
    error,
    // refetch 时重新加载（实际上数据已经静态 import 了，这里只是重置状态）
    refetch: loadData,
  };
}