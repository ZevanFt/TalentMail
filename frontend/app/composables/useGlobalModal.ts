export const useGlobalModal = () => {
  // 基础弹窗
  const isComposeOpen = useState('isComposeOpen', () => false)
  const isGenerateOpen = useState('isGenerateOpen', () => false) // 生成账号
  
  // 新增：账号池专用弹窗
  const isHistoryOpen = useState('isHistoryOpen', () => false)   // 验证历史
  const isStatsOpen = useState('isStatsOpen', () => false)       // 统计报表

  return { isComposeOpen, isGenerateOpen, isHistoryOpen, isStatsOpen }
}