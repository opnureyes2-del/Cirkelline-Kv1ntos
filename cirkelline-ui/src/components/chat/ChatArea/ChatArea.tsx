'use client'

import ChatInput from './ChatInput'
import MessageArea from './MessageArea'
import NoticeBanner from '@/components/NoticeBanner'
import { useStore } from '@/store'

const ChatArea = () => {
  const { messages } = useStore()
  const hasMessages = messages.length > 0

  return (
    <div className="flex flex-col h-full w-full relative">
      {/* Messages Area - Scrollable when has messages, centered when blank */}
      <div className={`flex-1 min-h-0 ${hasMessages ? 'overflow-y-auto' : 'overflow-hidden flex items-center justify-center'}`}>
        <MessageArea />
      </div>

      {/* Input Area - Sticky at bottom of chat container */}
      <div className="flex-shrink-0">
        <ChatInput />
      </div>

      {/* Notice Banner - Centered in chat area */}
      <NoticeBanner />
    </div>
  )
}

export default ChatArea
