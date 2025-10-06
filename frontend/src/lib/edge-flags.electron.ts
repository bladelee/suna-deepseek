// Electron版本的edge-flags，不依赖Vercel的Edge Config

export type IMaintenanceNotice =
  | {
      enabled: true;
      startTime: string; // Date
      endTime: string; // Date
    }
  | {
      enabled: false;
      startTime?: undefined;
      endTime?: undefined;
    };

// 模拟flag函数
const flag = <T>({ key, decide }: { key: string; decide: () => Promise<T> }) => {
  return decide;
};

export const maintenanceNoticeFlag = flag<IMaintenanceNotice>({
  key: 'maintenance-notice',
  async decide() {
    try {
      // 在Electron环境中总是返回disabled状态
      // 避免依赖Vercel Edge Config
      return { enabled: false } as const;
    } catch (cause) {
      console.error(
        new Error('Failed to get maintenance notice flag', { cause }),
      );
      return { enabled: false } as const;
    }
  },
});