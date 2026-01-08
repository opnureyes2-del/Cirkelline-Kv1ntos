/**
 * NotionTableView Component (FULLY DYNAMIC)
 * Displays Notion database items in a table format with ALL properties visible
 * Fetches schema from backend to generate columns dynamically
 */

import { useState, useEffect, useMemo, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  useReactTable,
  getCoreRowModel,
  ColumnDef,
  flexRender,
} from '@tanstack/react-table'
import { useVirtualizer } from '@tanstack/react-virtual'
import { ExternalLink, Loader2 } from 'lucide-react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  MouseSensor,
  TouchSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  useSortable,
  horizontalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { restrictToHorizontalAxis } from '@dnd-kit/modifiers'
import { useNotionData } from '@/hooks/useNotionData'

// Dynamic item type (can have any properties)
type NotionItem = Record<string, unknown>

interface NotionTableViewProps {
  items: NotionItem[]
  databaseType: 'tasks' | 'projects' | 'companies' | 'documentation'
}

// Schema cache to prevent refetching on every mount
const schemaCache: Record<string, NotionDatabaseSchema> = {}

interface NotionPropertySchema {
  id: string
  type: string
  name?: string
  [key: string]: unknown  // Type-specific configs (select options, etc.)
}

interface NotionDatabaseSchema {
  database_id: string
  database_title: string
  properties: Record<string, NotionPropertySchema>
  property_order?: string[]  // Property names in Notion's display order
  total_properties: number
}

/**
 * Format date for display
 */
function formatDate(dateString: string | undefined | null): string {
  if (!dateString) return '-'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  } catch {
    return String(dateString)
  }
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp: string | null | undefined): string {
  if (!timestamp) return '-'
  try {
    const date = new Date(timestamp)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return String(timestamp)
  }
}

/**
 * Extract text from Notion rich text or title property
 */
function extractText(value: unknown): string {
  if (!value) return ''
  if (typeof value === 'string') return value
  if (Array.isArray(value)) {
    return value.map(item => {
      if (typeof item === 'object' && item !== null) {
        const obj = item as Record<string, unknown>
        const text = obj.text as Record<string, unknown> | undefined
        return (text?.content as string) || (obj.plain_text as string) || ''
      }
      return ''
    }).join('')
  }
  if (typeof value === 'object' && value !== null) {
    const obj = value as Record<string, unknown>
    const text = obj.text as Record<string, unknown> | undefined
    if (text?.content) return String(text.content)
    if (obj.plain_text) return String(obj.plain_text)
  }
  return String(value)
}

/**
 * Get status/priority badge color based on value
 */
function getBadgeColor(value: string | undefined, type: 'status' | 'priority'): string {
  if (!value) return 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200'

  const lower = value.toLowerCase()

  if (type === 'status') {
    if (lower.includes('done') || lower.includes('completed')) {
      return 'bg-green-500/10 text-green-600 dark:text-green-400'
    }
    if (lower.includes('progress') || lower.includes('active')) {
      return 'bg-blue-500/10 text-blue-600 dark:text-blue-400'
    }
    if (lower.includes('todo') || lower.includes('not started')) {
      return 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200'
    }
  }

  if (type === 'priority') {
    if (lower.includes('high') || lower.includes('urgent')) {
      return 'bg-red-500/10 text-red-600 dark:text-red-400'
    }
    if (lower.includes('medium')) {
      return 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400'
    }
    if (lower.includes('low')) {
      return 'bg-green-500/10 text-green-600 dark:text-green-400'
    }
  }

  return 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200'
}

/**
 * Get column width based on property type
 * This provides sensible default widths for different Notion property types
 */
function getColumnWidth(propertyType: string): number {
  // Title columns need more space
  if (propertyType === 'title') return 300

  // Text-heavy columns
  if (propertyType === 'rich_text') return 250

  // Status/Select badges
  if (propertyType === 'status' || propertyType === 'select') return 150

  // Multi-select (tags can wrap)
  if (propertyType === 'multi_select' || propertyType === 'people') return 200

  // Dates
  if (propertyType === 'date' || propertyType === 'created_time' || propertyType === 'last_edited_time') return 180

  // Numbers
  if (propertyType === 'number') return 120

  // Checkboxes
  if (propertyType === 'checkbox') return 80

  // URLs
  if (propertyType === 'url' || propertyType === 'email') return 200

  // Relations
  if (propertyType === 'relation') return 120

  // Files
  if (propertyType === 'files') return 150

  // Default
  return 150
}

/**
 * Badge component
 */
function Badge({ children, className }: { children: React.ReactNode, className?: string }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${className}`}>
      {children}
    </span>
  )
}

/**
 * Render cell based on Notion property type
 */
function renderCellByType(value: unknown, propertyType: string): React.ReactNode {
  // Handle null/undefined
  if (value === null || value === undefined) {
    return <span className="text-light-text/50 dark:text-dark-text/50">-</span>
  }

  switch (propertyType) {
    case 'title':
    case 'rich_text':
      const text = extractText(value)
      return (
        <div className="truncate text-light-text dark:text-dark-text">
          {text || '-'}
        </div>
      )

    case 'number':
      return (
        <span className="text-light-text/70 dark:text-dark-text/70">
          {typeof value === 'number' ? value.toLocaleString() : (value ? String(value) : '-')}
        </span>
      )

    case 'select':
      const selectValue = typeof value === 'object' && value !== null ? (value as Record<string, unknown>).name : value
      return selectValue ? (
        <Badge className="bg-purple-500/10 text-purple-600 dark:text-purple-400">
          {String(selectValue)}
        </Badge>
      ) : (
        <span className="text-light-text/50 dark:text-dark-text/50">-</span>
      )

    case 'multi_select':
      if (!value || (Array.isArray(value) && value.length === 0)) {
        return <span className="text-light-text/50 dark:text-dark-text/50">-</span>
      }
      const tags = Array.isArray(value) ? value : [value]
      return (
        <div className="flex flex-wrap gap-1">
          {tags.map((tag: unknown, index: number) => {
            const tagName = typeof tag === 'object' && tag !== null ? (tag as Record<string, unknown>).name : tag
            return (
              <Badge key={index} className="bg-teal-500/10 text-teal-600 dark:text-teal-400">
                {String(tagName)}
              </Badge>
            )
          })}
        </div>
      )

    case 'status':
      const statusValue = typeof value === 'object' && value !== null ? (value as Record<string, unknown>).name : value
      return statusValue ? (
        <Badge className={getBadgeColor(String(statusValue), 'status')}>
          {String(statusValue)}
        </Badge>
      ) : (
        <span className="text-light-text/50 dark:text-dark-text/50">-</span>
      )

    case 'date':
      const dateValue = typeof value === 'object' && value !== null ? (value as Record<string, unknown>).start : value
      return (
        <span className="text-light-text/70 dark:text-dark-text/70 whitespace-nowrap">
          {formatDate(typeof dateValue === 'string' ? dateValue : null)}
        </span>
      )

    case 'checkbox':
      return (
        <div className="flex items-center justify-center">
          <input
            type="checkbox"
            checked={Boolean(value)}
            readOnly
            className="w-4 h-4 text-accent bg-light-bg dark:bg-dark-bg border-gray-300 dark:border-gray-600 rounded"
          />
        </div>
      )

    case 'url':
      return value ? (
        <a
          href={String(value)}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 dark:text-blue-400 hover:underline truncate block"
        >
          {String(value)}
        </a>
      ) : (
        <span className="text-light-text/50 dark:text-dark-text/50">-</span>
      )

    case 'email':
      return value ? (
        <a
          href={`mailto:${value}`}
          className="text-blue-600 dark:text-blue-400 hover:underline"
        >
          {String(value)}
        </a>
      ) : (
        <span className="text-light-text/50 dark:text-dark-text/50">-</span>
      )

    case 'phone_number':
      return value ? (
        <span className="text-light-text/70 dark:text-dark-text/70">
          {String(value)}
        </span>
      ) : (
        <span className="text-light-text/50 dark:text-dark-text/50">-</span>
      )

    case 'people':
      if (!value || (Array.isArray(value) && value.length === 0)) {
        return <span className="text-light-text/50 dark:text-dark-text/50">-</span>
      }
      const people = Array.isArray(value) ? value : [value]
      return (
        <div className="flex flex-wrap gap-1">
          {people.map((person: unknown, index: number) => {
            const personObj = typeof person === 'object' && person !== null ? person as Record<string, unknown> : null
            const name = personObj?.name || personObj?.email || 'Unknown'
            return (
              <Badge key={index} className="bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
                {String(name)}
              </Badge>
            )
          })}
        </div>
      )

    case 'files':
      if (!value || (Array.isArray(value) && value.length === 0)) {
        return <span className="text-light-text/50 dark:text-dark-text/50">-</span>
      }
      const files = Array.isArray(value) ? value : [value]
      return (
        <div className="flex flex-wrap gap-1">
          {files.map((file: unknown, index: number) => {
            const fileObj = typeof file === 'object' && file !== null ? file as Record<string, unknown> : null
            const fileName = fileObj?.name || `File ${index + 1}`
            return (
              <Badge key={index} className="bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200">
                {String(fileName)}
              </Badge>
            )
          })}
        </div>
      )

    case 'relation':
      if (!value || (Array.isArray(value) && value.length === 0)) {
        return <span className="text-light-text/50 dark:text-dark-text/50">-</span>
      }
      // Relations are just IDs for now (would need additional API call to resolve names)
      const relations = Array.isArray(value) ? value : [value]
      return (
        <span className="text-xs text-light-text/70 dark:text-dark-text/70">
          {relations.length} linked
        </span>
      )

    case 'formula':
    case 'rollup':
      // Display computed value
      return (
        <span className="text-light-text/70 dark:text-dark-text/70">
          {String(value)}
        </span>
      )

    case 'created_time':
    case 'last_edited_time':
      return (
        <span className="text-xs text-light-text/50 dark:text-dark-text/50 whitespace-nowrap">
          {formatTimestamp(typeof value === 'string' ? value : null)}
        </span>
      )

    case 'created_by':
    case 'last_edited_by':
      const userObj = typeof value === 'object' && value !== null ? value as Record<string, unknown> : null
      const userName = userObj?.name || userObj?.email || '-'
      return (
        <span className="text-xs text-light-text/70 dark:text-dark-text/70">
          {String(userName)}
        </span>
      )

    default:
      // Fallback: try to stringify
      try {
        const str = typeof value === 'object' ? JSON.stringify(value) : String(value)
        return (
          <span className="text-xs text-light-text/70 dark:text-dark-text/70 truncate max-w-[200px]">
            {str}
          </span>
        )
      } catch {
        return <span className="text-light-text/50 dark:text-dark-text/50">-</span>
      }
  }
}

/**
 * DraggableHeader Component
 * Renders a draggable column header with drag handle
 */
interface DraggableHeaderProps {
  headerId: string
  children: React.ReactNode
}

function DraggableHeader({ headerId, children }: DraggableHeaderProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: headerId })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    cursor: isDragging ? 'grabbing' : 'grab',
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex items-center gap-2"
      {...attributes}
      {...listeners}
    >
      {/* Drag handle icon */}
      <span className="text-light-text/30 dark:text-dark-text/30 hover:text-light-text/60 dark:hover:text-dark-text/60 transition-colors">
        ⋮⋮
      </span>
      {/* Header content */}
      <span>{children}</span>
    </div>
  )
}

/**
 * Generate columns from schema
 */
function useDynamicColumns(
  schema: NotionDatabaseSchema | null
): ColumnDef<NotionItem>[] {
  return useMemo(() => {
    if (!schema || !schema.properties) return []

    const columns: ColumnDef<NotionItem>[] = []
    const properties = schema.properties

    // Iterate through ALL properties in Notion's exact order (including title)
    // Use property_order array if available, otherwise fallback to Object.keys()
    const orderedPropertyNames = schema.property_order || Object.keys(properties)
    console.log('[useDynamicColumns] Using property order:', orderedPropertyNames)

    orderedPropertyNames.forEach((propName) => {
      const propConfig = properties[propName]
      if (!propConfig) return // Skip if property not in schema

      // Handle title column with special rendering (Notion link)
      if (propConfig.type === 'title') {
        columns.push({
          id: propName,
          header: propName,
          size: getColumnWidth(propConfig.type),
          minSize: 80,
          maxSize: 500,
          accessorFn: (row) => {
            // Try multiple keys for backward compatibility with old flat format
            const schemaKey = propName.toLowerCase().replace(/\s+/g, '_')
            return row[schemaKey] ?? row['title'] ?? row['name'] ?? row[propName] ?? null
          },
          cell: ({ row, getValue }) => {
            const value = getValue()
            const text = extractText(value)
            const itemUrl = typeof row.original.url === 'string' ? row.original.url : null
            return (
              <div className="flex items-center gap-2">
                <span className="truncate text-light-text dark:text-dark-text font-medium">
                  {text || 'Untitled'}
                </span>
                {itemUrl && (
                  <button
                    onClick={() => window.open(itemUrl, '_blank')}
                    className="flex-shrink-0 p-1 hover:bg-accent/10 rounded transition-colors"
                    title="Open in Notion"
                  >
                    <ExternalLink size={14} className="text-light-text/50 dark:text-dark-text/50" />
                  </button>
                )}
              </div>
            )
          },
        })
        return // Continue to next property
      }

      // All other column types
      columns.push({
        id: propName,
        header: propName,
        size: getColumnWidth(propConfig.type),
        minSize: 80,
        maxSize: 500,
        accessorFn: (row) => {
          // Try multiple naming conventions for backward compatibility
          const schemaKey = propName.toLowerCase().replace(/\s+/g, '_')

          // For common properties, try common aliases
          const propLower = propName.toLowerCase()
          if (propLower.includes('status')) {
            return row[schemaKey] ?? row['status'] ?? row[propName] ?? null
          }
          if (propLower.includes('priority')) {
            return row[schemaKey] ?? row['priority'] ?? row[propName] ?? null
          }
          if (propLower.includes('due') || propLower.includes('date')) {
            return row[schemaKey] ?? row['due_date'] ?? row['date'] ?? row[propName] ?? null
          }
          if (propLower.includes('description') || propLower.includes('notes')) {
            return row[schemaKey] ?? row['description'] ?? row['notes'] ?? row[propName] ?? null
          }

          // Default: try schema key, exact property name, then null
          return row[schemaKey] ?? row[propName] ?? null
        },
        cell: ({ getValue }) => {
          const value = getValue()
          return renderCellByType(value, propConfig.type)
        },
      })
    })

    return columns
  }, [schema])
}

/**
 * NotionTableView Component
 */
export default function NotionTableView({ items, databaseType }: NotionTableViewProps) {
  const [schema, setSchema] = useState<NotionDatabaseSchema | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [columnOrder, setColumnOrder] = useState<string[]>([])

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7777'

  // Get saveColumnOrder function from useNotionData hook
  const { saveColumnOrder } = useNotionData()

  // Configure drag sensors
  const sensors = useSensors(
    useSensor(MouseSensor, {
      activationConstraint: {
        distance: 8, // 8px movement to activate drag
      },
    }),
    useSensor(TouchSensor, {
      activationConstraint: {
        delay: 200, // 200ms hold to activate drag
        tolerance: 5,
      },
    }),
    useSensor(KeyboardSensor)
  )

  // Handle drag end
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      setColumnOrder((items) => {
        const oldIndex = items.indexOf(active.id as string)
        const newIndex = items.indexOf(over.id as string)

        const newOrder = arrayMove(items, oldIndex, newIndex)

        // Save to backend automatically
        console.log('[Column Order] New order:', newOrder)
        saveColumnOrder(databaseType, newOrder).then((success) => {
          if (success) {
            console.log('✅ Column order saved successfully')
          } else {
            console.error('❌ Failed to save column order')
          }
        })

        return newOrder
      })
    }
  }

  // Fetch schema on mount or when database type changes
  useEffect(() => {
    const fetchSchema = async () => {
      // Check cache first
      const cachedSchema = schemaCache[databaseType]
      if (cachedSchema) {
        console.log(`[NotionTableView] Using cached schema for ${databaseType}`)
        setSchema(cachedSchema)
        if (cachedSchema.property_order && cachedSchema.property_order.length > 0) {
          setColumnOrder(cachedSchema.property_order)
        }
        return
      }

      // Only set loading if fetching new schema
      setLoading(true)
      setError(null)

      try {
        const token = localStorage.getItem('token')
        if (!token) {
          throw new Error('Not authenticated')
        }

        const response = await fetch(
          `${apiUrl}/api/notion/databases/${databaseType}/schema`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }
        )

        if (!response.ok) {
          throw new Error(`Failed to fetch schema: ${response.statusText}`)
        }

        const data = await response.json()
        console.log(`[NotionTableView] Fetched schema for ${databaseType}:`, {
          property_order: data.property_order,
          properties_count: Object.keys(data.properties || {}).length
        })

        // Store in cache
        schemaCache[databaseType] = data

        setSchema(data)

        // Initialize column order from schema (or use saved order from backend)
        if (data.property_order && data.property_order.length > 0) {
          setColumnOrder(data.property_order)
        }
      } catch (err) {
        console.error('Schema fetch error:', err)
        setError(err instanceof Error ? err.message : 'Failed to load schema')
      } finally {
        setLoading(false)
      }
    }

    fetchSchema()
  }, [databaseType, apiUrl])

  const columns = useDynamicColumns(schema)

  const table = useReactTable({
    data: items,
    columns,
    getCoreRowModel: getCoreRowModel(),
    state: {
      columnOrder: columnOrder,
    },
    onColumnOrderChange: setColumnOrder,
  })

  const tableContainerRef = useRef<HTMLDivElement>(null)

  // Virtualizer for performance with large datasets
  const rowVirtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => tableContainerRef.current,
    estimateSize: () => 48,
    overscan: 10,
  })

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-6 h-6 animate-spin text-accent" />
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="px-6 py-12 text-center">
        <p className="text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
        <p className="text-xs text-light-text/60 dark:text-dark-text/60 mt-2">
          Try reconnecting your Notion workspace or syncing your databases.
        </p>
      </div>
    )
  }

  // Empty state
  if (items.length === 0) {
    return (
      <div className="px-6 py-12 text-center text-light-text/60 dark:text-dark-text/60">
        No {databaseType} found
      </div>
    )
  }

  // No schema
  if (!schema || columns.length === 0) {
    return (
      <div className="px-6 py-12 text-center text-light-text/60 dark:text-dark-text/60">
        No properties found for this database
      </div>
    )
  }

  return (
    <div
      ref={tableContainerRef}
      className="h-full overflow-auto email-scroll"
    >
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
        modifiers={[restrictToHorizontalAxis]}
      >
        <motion.table
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.5,
            ease: [0.4, 0, 0.2, 1]
          }}
          className="w-full border-collapse"
        >
          <thead className="sticky top-0 z-10 bg-light-bg dark:bg-dark-bg">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="border-b border-border-primary">
                <SortableContext
                  items={columnOrder}
                  strategy={horizontalListSortingStrategy}
                >
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-4 py-3 text-left text-xs font-medium text-light-text/70 dark:text-dark-text/70 uppercase tracking-wider"
                      style={{
                        width: `${header.getSize()}px`,
                        minWidth: `${header.getSize()}px`,
                        maxWidth: `${header.getSize()}px`,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      <DraggableHeader headerId={header.column.id}>
                        {flexRender(header.column.columnDef.header, header.getContext())}
                      </DraggableHeader>
                    </th>
                  ))}
                </SortableContext>
              </tr>
            ))}
          </thead>
        <tbody
          style={{
            height: `${rowVirtualizer.getTotalSize()}px`,
            position: 'relative',
          }}
        >
          {rowVirtualizer.getVirtualItems().map((virtualRow) => {
            const row = table.getRowModel().rows[virtualRow.index]
            return (
              <tr
                key={row.id}
                className="border-b border-border-primary hover:bg-light-bg/50 dark:hover:bg-dark-bg/50 transition-colors"
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: `${virtualRow.size}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                }}
              >
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className="px-4 py-3 text-sm text-left"
                    style={{
                      width: `${cell.column.getSize()}px`,
                      minWidth: `${cell.column.getSize()}px`,
                      maxWidth: `${cell.column.getSize()}px`,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            )
          })}
        </tbody>
        </motion.table>
      </DndContext>

      {/* Schema info (for debugging) */}
      {schema && (
        <div className="px-4 py-2 text-xs text-light-text/50 dark:text-dark-text/50 border-t border-border-primary">
          Showing {items.length} items with {schema.total_properties} properties from &quot;{schema.database_title}&quot;
        </div>
      )}
    </div>
  )
}
