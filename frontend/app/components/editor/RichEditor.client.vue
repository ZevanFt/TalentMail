<script setup lang="ts">
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'
import { Table } from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import { TextStyle } from '@tiptap/extension-text-style'
import Color from '@tiptap/extension-color'
import Highlight from '@tiptap/extension-highlight'
import TextAlign from '@tiptap/extension-text-align'
import Placeholder from '@tiptap/extension-placeholder'
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight'
import { common, createLowlight } from 'lowlight'
import { TemplateVariable } from './extensions/TemplateVariable'
import EditorToolbar from './EditorToolbar.vue'

const lowlight = createLowlight(common)

const props = withDefaults(
  defineProps<{
    modelValue?: string
    placeholder?: string
    showVariableBar?: boolean
    variables?: Array<{ key: string; label?: string }>
    minHeight?: number
    editable?: boolean
  }>(),
  {
    modelValue: '',
    placeholder: '',
    showVariableBar: false,
    variables: () => [],
    minHeight: 200,
    editable: true,
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const internalUpdate = ref(false)

const editor = useEditor({
  content: props.modelValue,
  editable: props.editable,
  extensions: [
    StarterKit.configure({
      codeBlock: false,
    }),
    Underline,
    Link.configure({
      openOnClick: false,
      autolink: true,
      HTMLAttributes: {
        class: 'text-blue-600 dark:text-blue-400 underline',
      },
    }),
    Image.configure({
      inline: true,
      allowBase64: true,
    }),
    Table.configure({
      resizable: true,
    }),
    TableRow,
    TableCell,
    TableHeader,
    TextStyle,
    Color,
    Highlight.configure({
      multicolor: true,
    }),
    TextAlign.configure({
      types: ['heading', 'paragraph'],
    }),
    Placeholder.configure({
      placeholder: props.placeholder,
    }),
    CodeBlockLowlight.configure({
      lowlight,
    }),
    TemplateVariable,
  ],
  onUpdate: ({ editor: ed }) => {
    internalUpdate.value = true
    emit('update:modelValue', ed.getHTML())
    nextTick(() => {
      internalUpdate.value = false
    })
  },
})

// 外部 modelValue 变化时同步（避免循环）
watch(
  () => props.modelValue,
  (val) => {
    if (internalUpdate.value) return
    const current = editor.value?.getHTML()
    if (val !== current) {
      editor.value?.commands.setContent(val || '', false)
    }
  }
)

watch(
  () => props.editable,
  (val) => {
    editor.value?.setEditable(val)
  }
)

const handleInsertVariable = (name: string) => {
  editor.value?.chain().focus().insertVariable(name).run()
}

const handleInsertImage = () => {
  // 图片插入现在由 EditorToolbar 内部的弹窗处理
  // 这里作为后备：如果通过其他方式触发，直接由 toolbar 内处理
}

// 暴露给父组件的方法
defineExpose({
  setContent: (html: string) => {
    editor.value?.commands.setContent(html, false)
  },
  getHTML: () => {
    return editor.value?.getHTML() || ''
  },
  getText: () => {
    return editor.value?.getText() || ''
  },
  insertVariable: (name: string) => {
    editor.value?.chain().focus().insertVariable(name).run()
  },
  insertContent: (content: string) => {
    editor.value?.chain().focus().insertContent(content).run()
  },
  focus: () => {
    editor.value?.commands.focus()
  },
  getEditor: () => editor.value,
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<template>
  <div class="rich-editor border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden bg-white dark:bg-gray-900">
    <EditorToolbar
      :editor="editor"
      :show-variable-bar="showVariableBar"
      :variables="variables"
      @insert-variable="handleInsertVariable"
      @insert-image="handleInsertImage"
    />
    <EditorContent
      :editor="editor"
      class="rich-editor-content"
      :style="{ minHeight: `${minHeight}px` }"
    />
  </div>
</template>

<style>
/* TipTap 编辑器样式 */
.rich-editor-content .tiptap {
  padding: 0.75rem 1rem;
  outline: none;
  min-height: inherit;
}

.rich-editor-content .tiptap p {
  margin: 0.25em 0;
}

.rich-editor-content .tiptap h1 {
  font-size: 1.5em;
  font-weight: 700;
  margin: 0.5em 0 0.25em;
}

.rich-editor-content .tiptap h2 {
  font-size: 1.25em;
  font-weight: 600;
  margin: 0.5em 0 0.25em;
}

.rich-editor-content .tiptap h3 {
  font-size: 1.1em;
  font-weight: 600;
  margin: 0.5em 0 0.25em;
}

.rich-editor-content .tiptap ul,
.rich-editor-content .tiptap ol {
  padding-left: 1.5em;
  margin: 0.25em 0;
}

.rich-editor-content .tiptap ul {
  list-style-type: disc;
}

.rich-editor-content .tiptap ol {
  list-style-type: decimal;
}

.rich-editor-content .tiptap blockquote {
  border-left: 3px solid #d1d5db;
  padding-left: 1em;
  margin: 0.5em 0;
  color: #6b7280;
}

.dark .rich-editor-content .tiptap blockquote {
  border-left-color: #4b5563;
  color: #9ca3af;
}

.rich-editor-content .tiptap pre {
  background: #1e293b;
  color: #e2e8f0;
  border-radius: 0.375rem;
  padding: 0.75em 1em;
  margin: 0.5em 0;
  font-family: ui-monospace, monospace;
  font-size: 0.875em;
  overflow-x: auto;
}

.rich-editor-content .tiptap code {
  background: #f1f5f9;
  border-radius: 0.25rem;
  padding: 0.125em 0.25em;
  font-size: 0.875em;
  font-family: ui-monospace, monospace;
}

.dark .rich-editor-content .tiptap code {
  background: #334155;
}

.rich-editor-content .tiptap pre code {
  background: transparent;
  padding: 0;
  border-radius: 0;
}

.rich-editor-content .tiptap img {
  max-width: 100%;
  height: auto;
  border-radius: 0.375rem;
  margin: 0.5em 0;
}

.rich-editor-content .tiptap table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5em 0;
}

.rich-editor-content .tiptap table td,
.rich-editor-content .tiptap table th {
  border: 1px solid #d1d5db;
  padding: 0.375em 0.75em;
  min-width: 80px;
}

.dark .rich-editor-content .tiptap table td,
.dark .rich-editor-content .tiptap table th {
  border-color: #4b5563;
}

.rich-editor-content .tiptap table th {
  background: #f9fafb;
  font-weight: 600;
}

.dark .rich-editor-content .tiptap table th {
  background: #1f2937;
}

.rich-editor-content .tiptap hr {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 1em 0;
}

.dark .rich-editor-content .tiptap hr {
  border-top-color: #374151;
}

.rich-editor-content .tiptap a {
  color: #2563eb;
  text-decoration: underline;
}

.dark .rich-editor-content .tiptap a {
  color: #60a5fa;
}

/* Placeholder */
.rich-editor-content .tiptap p.is-editor-empty:first-child::before {
  content: attr(data-placeholder);
  float: left;
  color: #9ca3af;
  pointer-events: none;
  height: 0;
}

.dark .rich-editor-content .tiptap p.is-editor-empty:first-child::before {
  color: #6b7280;
}
</style>
