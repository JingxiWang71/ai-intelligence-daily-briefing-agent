/**
 * utils.ts — shadcn/ui 的工具函数
 *
 * cn() 函数：合并多个 CSS 类名，并处理冲突。
 * 用于 shadcn/ui 组件中动态拼接 className。
 */

import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}