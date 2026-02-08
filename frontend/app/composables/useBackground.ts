/**
 * 自定义背景皮肤管理
 * 支持上传背景图片、调整透明度、模糊度等
 *
 * 订阅限制：此功能需要付费订阅才能使用
 * - 免费用户：只能预览，无法保存
 * - 付费用户：完整功能
 * - 管理员：无限制使用
 */
export interface BackgroundSettings {
  enabled: boolean          // 是否启用自定义背景
  imageUrl: string | null   // 背景图片URL（Base64或远程URL）
  opacity: number           // 背景透明度 0-100
  blur: number              // 模糊度 0-20
  overlayOpacity: number    // 叠加层透明度（用于增强文字可读性）
  position: 'center' | 'cover' | 'contain' | 'repeat' // 背景定位
  areas: {                  // 哪些区域显示背景
    sidebar: boolean        // 侧边栏
    header: boolean         // 顶部栏
    main: boolean           // 主内容区
    panels: boolean         // 面板/卡片
  }
}

const defaultSettings: BackgroundSettings = {
  enabled: false,
  imageUrl: null,
  opacity: 30,
  blur: 0,
  overlayOpacity: 60,
  position: 'cover',
  areas: {
    sidebar: true,
    header: true,
    main: true,
    panels: false,
  }
}

export const useBackground = () => {
  const { getSubscriptionStatus } = useApi()
  
  // 使用 useState 确保在不同组件间共享状态
  const settings = useState<BackgroundSettings>('backgroundSettings', () => ({ ...defaultSettings }))
  const isLoading = useState('backgroundLoading', () => false)
  
  // 订阅状态
  const canUseBackground = useState('canUseBackground', () => false)
  const subscriptionChecked = useState('subscriptionChecked', () => false)

  // 检查订阅权限
  const checkSubscription = async (): Promise<boolean> => {
    try {
      console.log('[Background] Checking subscription status...')
      const status = await getSubscriptionStatus()
      console.log('[Background] Subscription status:', status)
      
      // 管理员始终有权限
      if (status.is_admin) {
        console.log('[Background] Admin user detected, granting full access')
        canUseBackground.value = true
        subscriptionChecked.value = true
        return true
      }
      
      // 检查订阅状态和功能权限
      if (status.has_subscription && status.plan?.features) {
        const features = status.plan.features as Record<string, any>
        canUseBackground.value = features.allow_custom_background === true
        console.log('[Background] Subscription user, features:', features, 'canUse:', canUseBackground.value)
      } else {
        canUseBackground.value = false
        console.log('[Background] No subscription or features, denying access')
      }
      
      subscriptionChecked.value = true
      return canUseBackground.value
    } catch (e) {
      console.error('[Background] Failed to check subscription:', e)
      canUseBackground.value = false
      subscriptionChecked.value = true
      return false
    }
  }

  // 从本地存储初始化设置
  const initBackground = async () => {
    if (!import.meta.client) return
    
    console.log('[Background] Initializing background system...')
    
    // 先从 localStorage 加载设置（无论权限如何，先加载再说）
    const saved = localStorage.getItem('backgroundSettings')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        settings.value = { ...defaultSettings, ...parsed }
        console.log('[Background] Loaded settings from localStorage:', settings.value.enabled, !!settings.value.imageUrl)
        // 先应用背景（如果有保存的设置）
        if (settings.value.enabled && settings.value.imageUrl) {
          applyBackground()
        }
      } catch (e) {
        console.error('[Background] Failed to parse background settings:', e)
      }
    }
    
    // 然后检查订阅权限（用于设置页面的权限控制）
    await checkSubscription()
  }

  // 保存设置到本地存储（需要订阅权限）
  const saveSettings = (): boolean => {
    if (!import.meta.client) return false
    
    // 检查权限
    if (!canUseBackground.value) {
      console.warn('[Background] Custom background requires subscription')
      return false
    }
    
    localStorage.setItem('backgroundSettings', JSON.stringify(settings.value))
    applyBackground()
    return true
  }

  // 应用背景样式到 document
  const applyBackground = () => {
    if (!import.meta.client) return
    
    const root = document.documentElement
    
    if (!settings.value.enabled || !settings.value.imageUrl) {
      // 清除背景
      console.log('[Background] Clearing background')
      root.style.removeProperty('--bg-custom-image')
      root.style.removeProperty('--bg-custom-opacity')
      root.style.removeProperty('--bg-custom-blur')
      root.style.removeProperty('--bg-custom-overlay')
      root.classList.remove('has-custom-bg')
      return
    }

    console.log('[Background] Applying background, opacity:', settings.value.opacity)
    
    // 设置CSS变量
    root.style.setProperty('--bg-custom-image', `url(${settings.value.imageUrl})`)
    root.style.setProperty('--bg-custom-opacity', `${settings.value.opacity / 100}`)
    root.style.setProperty('--bg-custom-blur', `${settings.value.blur}px`)
    root.style.setProperty('--bg-custom-overlay', `${settings.value.overlayOpacity / 100}`)
    
    // 添加标记类
    root.classList.add('has-custom-bg')
    
    // 设置区域显示
    root.classList.toggle('bg-area-sidebar', settings.value.areas.sidebar)
    root.classList.toggle('bg-area-header', settings.value.areas.header)
    root.classList.toggle('bg-area-main', settings.value.areas.main)
    root.classList.toggle('bg-area-panels', settings.value.areas.panels)
    
    console.log('[Background] Applied! Classes:', root.classList.toString())
  }

  // 预览背景（临时应用，不保存）- 用于未订阅用户体验
  const previewBackground = (imageDataUrl: string) => {
    if (!import.meta.client) return
    
    console.log('[Background] Previewing background')
    const root = document.documentElement
    root.style.setProperty('--bg-custom-image', `url(${imageDataUrl})`)
    root.style.setProperty('--bg-custom-opacity', `${settings.value.opacity / 100}`)
    root.style.setProperty('--bg-custom-blur', `${settings.value.blur}px`)
    root.style.setProperty('--bg-custom-overlay', `${settings.value.overlayOpacity / 100}`)
    root.classList.add('has-custom-bg')
    
    // 预览时应用当前区域设置
    root.classList.toggle('bg-area-sidebar', settings.value.areas.sidebar)
    root.classList.toggle('bg-area-header', settings.value.areas.header)
    root.classList.toggle('bg-area-main', settings.value.areas.main)
    root.classList.toggle('bg-area-panels', settings.value.areas.panels)
  }

  // 清除预览
  const clearPreview = () => {
    if (!import.meta.client) return
    console.log('[Background] Clearing preview')
    // 如果没有保存的设置，清除所有
    if (!settings.value.enabled || !settings.value.imageUrl) {
      const root = document.documentElement
      root.style.removeProperty('--bg-custom-image')
      root.style.removeProperty('--bg-custom-opacity')
      root.style.removeProperty('--bg-custom-blur')
      root.style.removeProperty('--bg-custom-overlay')
      root.classList.remove('has-custom-bg')
      root.classList.remove('bg-area-sidebar', 'bg-area-header', 'bg-area-main', 'bg-area-panels')
    } else {
      // 恢复保存的设置
      applyBackground()
    }
  }

  // 压缩图片
  const compressImage = (file: File, maxWidth = 1920, quality = 0.8): Promise<string> => {
    return new Promise((resolve, reject) => {
      const img = new Image()
      const reader = new FileReader()
      
      reader.onload = (e) => {
        img.src = e.target?.result as string
      }
      
      reader.onerror = () => reject(new Error('读取图片失败'))
      reader.readAsDataURL(file)
      
      img.onload = () => {
        const canvas = document.createElement('canvas')
        let { width, height } = img
        
        // 等比例缩放
        if (width > maxWidth) {
          height = (height * maxWidth) / width
          width = maxWidth
        }
        
        canvas.width = width
        canvas.height = height
        
        const ctx = canvas.getContext('2d')
        if (!ctx) {
          reject(new Error('无法创建画布'))
          return
        }
        
        ctx.drawImage(img, 0, 0, width, height)
        
        // 转换为 JPEG 格式以减小体积
        const compressedDataUrl = canvas.toDataURL('image/jpeg', quality)
        resolve(compressedDataUrl)
      }
      
      img.onerror = () => reject(new Error('图片加载失败'))
    })
  }

  // 上传图片（压缩后转换为Base64存储在localStorage）
  const uploadImage = async (file: File, previewOnly = false): Promise<string> => {
    if (!file.type.startsWith('image/')) {
      throw new Error('请上传图片文件')
    }

    // 限制文件大小为 10MB（压缩前）
    if (file.size > 10 * 1024 * 1024) {
      throw new Error('图片大小不能超过 10MB')
    }

    isLoading.value = true
    
    try {
      // 压缩图片
      const compressedDataUrl = await compressImage(file)
      
      // 检查压缩后的大小（Base64 约为原大小的 1.37 倍，localStorage 限制约 5MB）
      const sizeInBytes = compressedDataUrl.length * 0.75 // Base64 转实际大小
      if (sizeInBytes > 2 * 1024 * 1024) {
        // 如果还是太大，用更低的质量重新压缩
        const furtherCompressed = await compressImage(file, 1280, 0.6)
        if (furtherCompressed.length * 0.75 > 2 * 1024 * 1024) {
          throw new Error('图片太大，请选择更小的图片')
        }
        
        if (previewOnly) {
          previewBackground(furtherCompressed)
          return furtherCompressed
        }
        
        if (!canUseBackground.value) {
          throw new Error('此功能需要订阅会员')
        }
        
        settings.value.imageUrl = furtherCompressed
        settings.value.enabled = true
        saveSettings()
        return furtherCompressed
      }
      
      if (previewOnly) {
        previewBackground(compressedDataUrl)
        return compressedDataUrl
      }
      
      if (!canUseBackground.value) {
        throw new Error('此功能需要订阅会员')
      }
      
      settings.value.imageUrl = compressedDataUrl
      settings.value.enabled = true
      saveSettings()
      return compressedDataUrl
    } finally {
      isLoading.value = false
    }
  }

  // 从URL加载图片
  const setImageUrl = (url: string) => {
    settings.value.imageUrl = url
    settings.value.enabled = true
    saveSettings()
  }

  // 清除背景
  const clearBackground = () => {
    settings.value.imageUrl = null
    settings.value.enabled = false
    saveSettings()
  }

  // 更新设置
  const updateSettings = (updates: Partial<BackgroundSettings>) => {
    settings.value = { ...settings.value, ...updates }
    saveSettings()
  }

  // 更新区域设置
  const updateAreas = (area: keyof BackgroundSettings['areas'], value: boolean) => {
    settings.value.areas[area] = value
    saveSettings()
  }

  // 重置为默认
  const resetToDefault = () => {
    settings.value = { ...defaultSettings }
    saveSettings()
  }

  return {
    settings,
    isLoading,
    canUseBackground,
    subscriptionChecked,
    checkSubscription,
    initBackground,
    uploadImage,
    setImageUrl,
    clearBackground,
    updateSettings,
    updateAreas,
    resetToDefault,
    previewBackground,
    clearPreview,
  }
}