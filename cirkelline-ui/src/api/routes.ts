// Helper to ensure URL doesn't have double slashes from trailing slash in base
const sanitizeUrl = (url: string): string => url.replace(/([^:]\/)\/+/g, '$1')

export const APIRoutes = {
  GetAgents: (agentOSUrl: string) => sanitizeUrl(`${agentOSUrl}/agents`),

  // CKC Folder Switcher endpoints
  GetCKCFolders: (agentOSUrl: string) => sanitizeUrl(`${agentOSUrl}/api/ckc/folders`),
  GetCKCCurrentFolder: (agentOSUrl: string) => sanitizeUrl(`${agentOSUrl}/api/ckc/folders/current`),
  SwitchCKCFolder: (agentOSUrl: string) => sanitizeUrl(`${agentOSUrl}/api/ckc/folders/switch`),
  GetCKCFolderById: (agentOSUrl: string, folderId: string) => sanitizeUrl(`${agentOSUrl}/api/ckc/folders/${folderId}`),
  GetCKCFolderContents: (agentOSUrl: string, folderId: string) => sanitizeUrl(`${agentOSUrl}/api/ckc/folders/${folderId}/contents`),
  GetCKCFavorites: (agentOSUrl: string) => sanitizeUrl(`${agentOSUrl}/api/ckc/folders/favorites`),
  ToggleCKCFavorite: (agentOSUrl: string, folderId: string) => sanitizeUrl(`${agentOSUrl}/api/ckc/folders/favorites/${folderId}`),
  GetCKCRecent: (agentOSUrl: string) => sanitizeUrl(`${agentOSUrl}/api/ckc/folders/recent`),
  GetCKCStatus: (agentOSUrl: string) => sanitizeUrl(`${agentOSUrl}/api/ckc/folders/status`),
  AgentRun: (agentOSUrl: string) => sanitizeUrl(`${agentOSUrl}/agents/{agent_id}/runs`),
  Status: (agentOSUrl: string) => sanitizeUrl(`${agentOSUrl}/health`),
  GetSessions: (agentOSUrl: string) => sanitizeUrl(`${agentOSUrl}/sessions`),
  GetSession: (agentOSUrl: string, sessionId: string) =>
    sanitizeUrl(`${agentOSUrl}/sessions/${sessionId}/runs`),
  GetSessionDetails: (agentOSUrl: string, sessionId: string) =>
    sanitizeUrl(`${agentOSUrl}/sessions/${sessionId}`),

  DeleteSession: (agentOSUrl: string, sessionId: string) =>
    sanitizeUrl(`${agentOSUrl}/sessions/${sessionId}`),
  BulkDeleteSessions: (agentOSUrl: string) => sanitizeUrl(`${agentOSUrl}/sessions`),

  GetTeams: (agentOSUrl: string) => sanitizeUrl(`${agentOSUrl}/teams`),
  TeamRun: (agentOSUrl: string, teamId: string) =>
    sanitizeUrl(`${agentOSUrl}/teams/${teamId}/runs`),
  CancelTeamRun: (agentOSUrl: string, teamId: string, runId: string) =>
    sanitizeUrl(`${agentOSUrl}/teams/${teamId}/runs/${runId}/cancel`),
  DeleteTeamSession: (agentOSUrl: string, teamId: string, sessionId: string) =>
    sanitizeUrl(`${agentOSUrl}/v1/teams/${teamId}/sessions/${sessionId}`)
}
