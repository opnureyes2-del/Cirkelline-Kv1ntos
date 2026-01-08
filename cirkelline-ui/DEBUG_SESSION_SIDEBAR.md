# Debug Session Sidebar Issue

## Problem
Only the first session shows in the sidebar. Second and subsequent sessions don't appear.

## FIXED: Authentication Bug (2025-10-11)

**Root Cause:** Backend login/register endpoints were using wrong column name
- Code was querying `password_hash`
- Database column is actually named `hashed_password`
- This caused 500 error on login and 400 error on register

**Fix Applied:**
- Updated `/home/eenvy/Desktop/cirkelline/my_os.py` lines 1168, 1175, 1285
- Changed `password_hash` to `hashed_password` in both signup and login SQL queries
- Backend restarted successfully

**Status:** Backend now running correctly. Need to test login/register and session creation.

## Debug Logging Added

### 1. useSessionLoader.tsx (getSessions function)
Added logging to track the merge operation:
- Previous sessions count
- Fetched sessions count
- Session IDs from both
- Optimistic sessions kept
- Final merged count

**Look for:** `🔍 SESSION MERGE DEBUG:` in browser console

### 2. useAIStreamHandler.tsx (optimistic session add)
Added logging to track when sessions are optimistically added:
- Current sessionId from URL
- New session_id from stream chunk
- Whether condition passes
- Session data being added
- Previous sessions count
- Whether session already exists
- New sessions count after add

**Look for:** `✨ OPTIMISTIC SESSION ADD:` in browser console

## Testing Steps

1. Start localhost dev server:
```bash
cd /home/eenvy/Desktop/cirkelline/cirkelline-ui
pnpm dev
```

2. Open browser console (F12)

3. Clear all sessions/start fresh

4. Send first message "hey"
   - Watch for `✨ OPTIMISTIC SESSION ADD:` logs
   - Check if session appears in sidebar

5. Click "New Chat" button

6. Send second message "hello"
   - Watch for `✨ OPTIMISTIC SESSION ADD:` logs
   - Watch for `🔍 SESSION MERGE DEBUG:` logs
   - Check if BOTH sessions appear in sidebar

## What to Look For

### Expected Behavior:
1. First message:
   - `✨ OPTIMISTIC SESSION ADD:` shows sessionId=null, new session added
   - Session appears in sidebar immediately

2. Second message:
   - `✨ OPTIMISTIC SESSION ADD:` shows sessionId=null (after clearChat), new session added
   - `🔍 SESSION MERGE DEBUG:` shows:
     - Previous sessions: 1 (the optimistic one)
     - Fetched sessions: 1 (the first one from DB)
     - Optimistic sessions kept: 1 (the second one not in DB yet)
     - Final merged count: 2
   - BOTH sessions should be in sidebar

### Possible Issues to Check:

1. **Optimistic add not triggering:**
   - Check if `✨ OPTIMISTIC SESSION ADD:` appears for second message
   - If not, condition on line 182-184 is failing
   - Check `sessionId` value - should be null after "New Chat"

2. **Merge wiping out optimistic session:**
   - Check `🔍 SESSION MERGE DEBUG:` logs
   - If "Optimistic sessions kept: 0", the new session IS in fetched data (shouldn't be)
   - If "Final merged count" is wrong, merge logic has issue

3. **getSessions called too frequently:**
   - Check how many times `🔍 SESSION MERGE DEBUG:` appears
   - If it's called multiple times rapidly, it might be clearing the optimistic session

4. **Session ID mismatch:**
   - Check if session IDs match between optimistic add and fetched data
   - They should be different (optimistic is new, fetched is old)

## Potential Root Causes

### Theory 1: sessionId not cleared on "New Chat"
- Check useChatActions clearChat() - does it set sessionId to null?
- Line 56 should be: `setSessionId(null)`

### Theory 2: getSessions called immediately after optimistic add
- Check Sessions.tsx useEffect dependencies (lines 95-117)
- If agentId/teamId/mode/etc changes, it triggers getSessions
- This might happen BEFORE the optimistic session is added

### Theory 3: Condition not passing on second message
- Line 183: `(!sessionId || sessionId !== chunk.session_id)`
- If sessionId is not null when it should be, condition fails
- Check if setSessionId(null) in clearChat is working

## Next Steps Based on Logs

1. If optimistic add not triggering:
   → Fix the condition or clearChat function

2. If optimistic session being wiped out:
   → Check merge logic, ensure new session ID not in fetched data

3. If multiple getSessions calls:
   → Add debouncing or prevent unnecessary calls

## Files Modified

- `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/hooks/useSessionLoader.tsx`
- `/home/eenvy/Desktop/cirkelline/cirkelline-ui/src/hooks/useAIStreamHandler.tsx`

## To Remove Debug Logs Later

Search for:
- `console.log('🔍 SESSION MERGE DEBUG:')`
- `console.log('✨ OPTIMISTIC SESSION ADD:')`

And remove those console.log blocks.
