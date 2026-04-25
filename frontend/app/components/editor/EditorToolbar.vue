<script setup lang="ts">
import type { Editor } from '@tiptap/vue-3'
import {
  Bold, Italic, Underline, Strikethrough,
  Heading1, Heading2, Heading3,
  List, ListOrdered, Quote, Code2,
  AlignLeft, AlignCenter, AlignRight,
  ImagePlus, Table, Link2, Minus,
  Paintbrush, Highlighter, Eraser,
  Variable,
} from 'lucide-vue-next'

const props = defineProps<{
  editor: Editor | undefined
  showVariableBar?: boolean
  variables?: Array<{ key: string; label?: string }>
}>()

const emit = defineEmits<{
  (e: 'insert-variable', name: string): void
  (e: 'insert-image'): void
}>()

const colorInput = ref<HTMLInputElement | null>(null)
const highlightInput = ref<HTMLInputElement | null>(null)

// 内联输入弹窗状态（替代 window.prompt）
const showInputPopover = ref(false)
const inputPopoverType = ref<'link' | 'image'>('link')
const inputPopoverValue = ref('')
const inputPopoverRef = ref<HTMLInputElement | null>(null)
const inputPopoverLabel = computed(() => inputPopoverType.value === 'link' ? '链接 URL' : '图片 URL')
const inputPopoverPlaceholder = computed(() => inputPopoverType.value === 'link' ? 'https://example.com' : 'https://example.com/image.png')

const openInputPopover = (type: 'link' | 'image', defaultValue = '') => {
  inputPopoverType.value = type
  inputPopoverValue.value = defaultValue
  showInputPopover.value = true
  nextTick(() => inputPopoverRef.value?.focus())
}

const confirmInputPopover = () => {
  const url = inputPopoverValue.value.trim()
  showInputPopover.value = false

  if (inputPopoverType.value === 'link') {
    if (!props.editor) return
    if (url === '') {
      props.editor.chain().focus().extendMarkRange('link').unsetLink().run()
    } else {
      props.editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
    }
  } else {
    // image
    if (url) {
      props.editor?.chain().focus().setImage({ src: url }).run()
    }
  }
}

const cancelInputPopover = () => {
  showInputPopover.value = false
}

const handleLink = () => {
  if (!props.editor) return
  const prev = props.editor.getAttributes('link').href
  openInputPopover('link', prev || 'https://')
}

const handleImage = () => {
  openInputPopover('image', 'https://')
}

const handleTable = () => {
  props.editor?.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
}

const setColor = (e: Event) => {
  const target = e.target as HTMLInputElement
  props.editor?.chain().focus().setColor(target.value).run()
}

const setHighlight = (e: Event) => {
  const target = e.target as HTMLInputElement
  props.editor?.chain().focus().toggleHighlight({ color: target.value }).run()
}

interface ToolBtn {
  icon: any
  title: string
  action: () => void
  isActive?: () => boolean
}

const formatBtns = computed<ToolBtn[]>(() => {
  const e = props.editor
  if (!e) return []
  return [
    { icon: Bold, title: '加粗', action: () => e.chain().focus().toggleBold().run(), isActive: () => e.isActive('bold') },
    { icon: Italic, title: '斜体', action: () => e.chain().focus().toggleItalic().run(), isActive: () => e.isActive('italic') },
    { icon: Underline, title: '下划线', action: () => e.chain().focus().toggleUnderline().run(), isActive: () => e.isActive('underline') },
    { icon: Strikethrough, title: '删除线', action: () => e.chain().focus().toggleStrike().run(), isActive: () => e.isActive('strike') },
  ]
})

const headingBtns = computed<ToolBtn[]>(() => {
  const e = props.editor
  if (!e) return []
  return [
    { icon: Heading1, title: 'H1', action: () => e.chain().focus().toggleHeading({ level: 1 }).run(), isActive: () => e.isActive('heading', { level: 1 }) },
    { icon: Heading2, title: 'H2', action: () => e.chain().focus().toggleHeading({ level: 2 }).run(), isActive: () => e.isActive('heading', { level: 2 }) },
    { icon: Heading3, title: 'H3', action: () => e.chain().focus().toggleHeading({ level: 3 }).run(), isActive: () => e.isActive('heading', { level: 3 }) },
  ]
})

const blockBtns = computed<ToolBtn[]>(() => {
  const e = props.editor
  if (!e) return []
  return [
    { icon: List, title: '无序列表', action: () => e.chain().focus().toggleBulletList().run(), isActive: () => e.isActive('bulletList') },
    { icon: ListOrdered, title: '有序列表', action: () => e.chain().focus().toggleOrderedList().run(), isActive: () => e.isActive('orderedList') },
    { icon: Quote, title: '引用', action: () => e.chain().focus().toggleBlockquote().run(), isActive: () => e.isActive('blockquote') },
    { icon: Code2, title: '代码块', action: () => e.chain().focus().toggleCodeBlock().run(), isActive: () => e.isActive('codeBlock') },
  ]
})

const alignBtns = computed<ToolBtn[]>(() => {
  const e = props.editor
  if (!e) return []
  return [
    { icon: AlignLeft, title: '左对齐', action: () => e.chain().focus().setTextAlign('left').run(), isActive: () => e.isActive({ textAlign: 'left' }) },
    { icon: AlignCenter, title: '居中', action: () => e.chain().focus().setTextAlign('center').run(), isActive: () => e.isActive({ textAlign: 'center' }) },
    { icon: AlignRight, title: '右对齐', action: () => e.chain().focus().setTextAlign('right').run(), isActive: () => e.isActive({ textAlign: 'right' }) },
  ]
})

const insertBtns = computed<ToolBtn[]>(() => {
  const e = props.editor
  if (!e) return []
  return [
    { icon: ImagePlus, title: '插入图片', action: handleImage },
    { icon: Table, title: '插入表格', action: handleTable },
    { icon: Link2, title: '链接', action: handleLink, isActive: () => e.isActive('link') },
    { icon: Minus, title: '分割线', action: () => e.chain().focus().setHorizontalRule().run() },
  ]
})
</script>

<template>
  <div v-if="editor" class="flex flex-wrap items-center gap-0.5 px-2 py-1.5 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
    <!-- 文字格式 -->
    <template v-for="btn in formatBtns" :key="btn.title">
      <button
        type="button"
        :title="btn.title"
        class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        :class="btn.isActive?.() ? 'bg-gray-200 dark:bg-gray-700 text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'"
        @click="btn.action"
      >
        <component :is="btn.icon" class="w-4 h-4" />
      </button>
    </template>

    <div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-1" />

    <!-- 标题 -->
    <template v-for="btn in headingBtns" :key="btn.title">
      <button
        type="button"
        :title="btn.title"
        class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        :class="btn.isActive?.() ? 'bg-gray-200 dark:bg-gray-700 text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'"
        @click="btn.action"
      >
        <component :is="btn.icon" class="w-4 h-4" />
      </button>
    </template>

    <div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-1" />

    <!-- 列表/引用/代码 -->
    <template v-for="btn in blockBtns" :key="btn.title">
      <button
        type="button"
        :title="btn.title"
        class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        :class="btn.isActive?.() ? 'bg-gray-200 dark:bg-gray-700 text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'"
        @click="btn.action"
      >
        <component :is="btn.icon" class="w-4 h-4" />
      </button>
    </template>

    <div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-1" />

    <!-- 对齐 -->
    <template v-for="btn in alignBtns" :key="btn.title">
      <button
        type="button"
        :title="btn.title"
        class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        :class="btn.isActive?.() ? 'bg-gray-200 dark:bg-gray-700 text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'"
        @click="btn.action"
      >
        <component :is="btn.icon" class="w-4 h-4" />
      </button>
    </template>

    <div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-1" />

    <!-- 颜色 -->
    <div class="relative">
      <button type="button" title="文字颜色" class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors" @click="colorInput?.click()">
        <Paintbrush class="w-4 h-4" />
      </button>
      <input ref="colorInput" type="color" class="absolute w-0 h-0 opacity-0" @input="setColor" />
    </div>
    <div class="relative">
      <button type="button" title="高亮" class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors" @click="highlightInput?.click()">
        <Highlighter class="w-4 h-4" />
      </button>
      <input ref="highlightInput" type="color" value="#fef08a" class="absolute w-0 h-0 opacity-0" @input="setHighlight" />
    </div>

    <div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-1" />

    <!-- 插入 -->
    <template v-for="btn in insertBtns" :key="btn.title">
      <button
        type="button"
        :title="btn.title"
        class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
        :class="btn.isActive?.() ? 'bg-gray-200 dark:bg-gray-700 text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'"
        @click="btn.action"
      >
        <component :is="btn.icon" class="w-4 h-4" />
      </button>
    </template>

    <div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-1" />

    <!-- 清除格式 -->
    <button
      type="button"
      title="清除格式"
      class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-colors"
      @click="editor.chain().focus().clearNodes().unsetAllMarks().run()"
    >
      <Eraser class="w-4 h-4" />
    </button>

    <!-- 内联 URL 输入弹窗 -->
    <Teleport to="body">
      <div v-if="showInputPopover" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="cancelInputPopover">
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 p-4 w-96 animate-in fade-in zoom-in-95 duration-150">
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">{{ inputPopoverLabel }}</label>
          <input
            ref="inputPopoverRef"
            v-model="inputPopoverValue"
            type="url"
            :placeholder="inputPopoverPlaceholder"
            class="w-full px-3 py-2 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-sm outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
            @keydown.enter.prevent="confirmInputPopover"
            @keydown.escape.prevent="cancelInputPopover"
          />
          <div class="flex justify-end gap-2 mt-3">
            <button
              type="button"
              class="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              @click="cancelInputPopover"
            >取消</button>
            <button
              type="button"
              class="px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary-hover transition-colors"
              @click="confirmInputPopover"
            >确认</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 模板变量栏 -->
    <template v-if="showVariableBar && variables?.length">
      <div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-1" />
      <div class="flex items-center gap-1 flex-wrap">
        <span class="text-xs text-gray-500 dark:text-gray-400 mr-0.5">
          <Variable class="w-3.5 h-3.5 inline" /> 变量:
        </span>
        <button
          v-for="v in variables"
          :key="v.key"
          type="button"
          class="px-1.5 py-0.5 text-xs rounded bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-700 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors font-mono"
          @click="emit('insert-variable', v.key)"
        >
          {{ v.label || v.key }}
        </button>
      </div>
    </template>
  </div>
</template>
