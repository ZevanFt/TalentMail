import { Node, mergeAttributes } from '@tiptap/core'

export interface TemplateVariableOptions {
  HTMLAttributes: Record<string, any>
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    templateVariable: {
      insertVariable: (name: string) => ReturnType
    }
  }
}

export const TemplateVariable = Node.create<TemplateVariableOptions>({
  name: 'templateVariable',
  group: 'inline',
  inline: true,
  atom: true,
  selectable: true,
  draggable: true,

  addOptions() {
    return {
      HTMLAttributes: {},
    }
  },

  addAttributes() {
    return {
      name: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-template-var'),
        renderHTML: (attributes) => ({
          'data-template-var': attributes.name,
        }),
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-template-var]',
      },
    ]
  },

  renderHTML({ node, HTMLAttributes }) {
    return [
      'span',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        'data-template-var': node.attrs.name,
        class:
          'inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded text-xs font-mono font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 border border-blue-200 dark:border-blue-700 cursor-default select-none',
        contenteditable: 'false',
      }),
      `{{${node.attrs.name}}}`,
    ]
  },

  addCommands() {
    return {
      insertVariable:
        (name: string) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: { name },
          })
        },
    }
  },
})

export default TemplateVariable
