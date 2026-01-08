'use client'

import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { ChevronLeft, ChevronRight, X } from 'lucide-react'

interface DateRangePickerProps {
  fromDate: Date | null
  toDate: Date | null
  onFromDateChange: (date: Date | null) => void
  onToDateChange: (date: Date | null) => void
  onClose: () => void
}

export default function DateRangePicker({
  fromDate,
  toDate,
  onFromDateChange,
  onToDateChange,
  onClose
}: DateRangePickerProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [selectingFrom, setSelectingFrom] = useState(true)

  // Generate calendar days for current month
  const calendarDays = useMemo(() => {
    const year = currentMonth.getFullYear()
    const month = currentMonth.getMonth()

    // First day of month
    const firstDay = new Date(year, month, 1)
    const startingDayOfWeek = firstDay.getDay() // 0 = Sunday

    // Last day of month
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()

    const days = []

    // Add empty slots for days before first day
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null)
    }

    // Add all days in month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day))
    }

    return days
  }, [currentMonth])

  const handleDateClick = (date: Date) => {
    if (selectingFrom) {
      onFromDateChange(date)
      setSelectingFrom(false)
    } else {
      // If selecting "to" date and it's before "from" date, swap them
      if (fromDate && date < fromDate) {
        onToDateChange(fromDate)
        onFromDateChange(date)
      } else {
        onToDateChange(date)
      }
      setSelectingFrom(true)
    }
  }

  const isDateInRange = (date: Date) => {
    if (!fromDate || !toDate) return false
    return date >= fromDate && date <= toDate
  }

  const isDateSelected = (date: Date) => {
    if (!fromDate && !toDate) return false
    return (
      (fromDate && date.toDateString() === fromDate.toDateString()) ||
      (toDate && date.toDateString() === toDate.toDateString())
    )
  }

  const isToday = (date: Date) => {
    const today = new Date()
    return date.toDateString() === today.toDateString()
  }

  const goToPreviousMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))
  }

  const goToNextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))
  }

  const clearDates = () => {
    onFromDateChange(null)
    onToDateChange(null)
    setSelectingFrom(true)
  }

  const monthName = currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.2 }}
      className="absolute top-full left-0 mt-2 z-50 backdrop-blur-xl
                 bg-light-bg/80 dark:bg-dark-bg/80
                 border border-border-primary rounded-2xl shadow-2xl p-6 min-w-[380px]"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-light-text dark:text-dark-text font-heading">
          {selectingFrom ? 'Select From Date' : 'Select To Date'}
        </h3>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary
                   text-light-text-secondary dark:text-dark-text-secondary transition-colors"
        >
          <X size={18} />
        </button>
      </div>

      {/* Selected Range Display */}
      {(fromDate || toDate) && (
        <div className="mb-4 p-3 rounded-lg bg-accent/5 border border-accent/20">
          <div className="flex items-center justify-between">
            <div className="flex gap-4 text-sm">
              <div>
                <span className="text-light-text-secondary dark:text-dark-text-secondary">From: </span>
                <span className="font-semibold text-light-text dark:text-dark-text">
                  {fromDate ? fromDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Not selected'}
                </span>
              </div>
              <div>
                <span className="text-light-text-secondary dark:text-dark-text-secondary">To: </span>
                <span className="font-semibold text-light-text dark:text-dark-text">
                  {toDate ? toDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Not selected'}
                </span>
              </div>
            </div>
            <button
              onClick={clearDates}
              className="text-xs text-accent hover:text-accent/80 font-medium transition-colors"
            >
              Clear
            </button>
          </div>
        </div>
      )}

      {/* Month Navigation */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={goToPreviousMonth}
          className="p-2 rounded-lg hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary
                   text-light-text dark:text-dark-text transition-colors"
        >
          <ChevronLeft size={20} />
        </button>
        <span className="text-base font-semibold text-light-text dark:text-dark-text">
          {monthName}
        </span>
        <button
          onClick={goToNextMonth}
          className="p-2 rounded-lg hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary
                   text-light-text dark:text-dark-text transition-colors"
        >
          <ChevronRight size={20} />
        </button>
      </div>

      {/* Week Days Header */}
      <div className="grid grid-cols-7 gap-2 mb-2">
        {weekDays.map(day => (
          <div
            key={day}
            className="text-center text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-2">
        {calendarDays.map((date, index) => {
          if (!date) {
            return <div key={`empty-${index}`} className="aspect-square" />
          }

          const selected = isDateSelected(date)
          const inRange = isDateInRange(date)
          const today = isToday(date)

          return (
            <motion.button
              key={date.toISOString()}
              onClick={() => handleDateClick(date)}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className={`aspect-square rounded-lg text-sm font-medium transition-all
                ${selected
                  ? 'bg-accent text-white shadow-md'
                  : inRange
                  ? 'bg-accent/20 text-accent'
                  : today
                  ? 'bg-light-bg-secondary dark:bg-dark-bg-secondary text-accent font-bold'
                  : 'text-light-text dark:text-dark-text hover:bg-light-bg-secondary dark:hover:bg-dark-bg-secondary'
                }
              `}
            >
              {date.getDate()}
            </motion.button>
          )
        })}
      </div>

      {/* Footer Instructions */}
      <div className="mt-4 pt-4 border-t border-border-primary">
        <p className="text-xs text-center text-light-text-secondary dark:text-dark-text-secondary">
          Click a date to select {selectingFrom ? 'start' : 'end'} of range
        </p>
      </div>
    </motion.div>
  )
}
