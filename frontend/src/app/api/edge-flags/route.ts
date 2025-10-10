import { NextResponse } from 'next/server';
import { maintenanceNoticeFlag } from '@/lib/edge-flags';

// 配置为静态生成，适合静态导出
export const dynamic = 'force-static';
// 设置重验证时间为10分钟
export const revalidate = 600;

export async function GET() {
  try {
    const maintenanceNotice = await maintenanceNoticeFlag();
    return NextResponse.json(maintenanceNotice);
  } catch (error) {
    console.error('Error fetching maintenance notice:', error);
    // 出错时返回一个默认的禁用状态
    return NextResponse.json({ enabled: false });
  }
}
