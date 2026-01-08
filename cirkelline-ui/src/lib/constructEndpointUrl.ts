/**
 * Remove trailing slashes from a URL to prevent double-slash issues
 * when concatenating with route paths
 */
const removeTrailingSlash = (url: string): string => {
  return url.replace(/\/+$/, '')
}

export const constructEndpointUrl = (
  value: string | null | undefined
): string => {
  if (!value) return ''

  let url: string

  if (value.startsWith('http://') || value.startsWith('https://')) {
    url = decodeURIComponent(value)
  } else if (
    // Check if the endpoint is localhost or an IP address
    value.startsWith('localhost') ||
    /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/.test(value)
  ) {
    url = `http://${decodeURIComponent(value)}`
  } else {
    // For all other cases, default to HTTPS
    url = `https://${decodeURIComponent(value)}`
  }

  // Always remove trailing slashes to prevent //path issues
  return removeTrailingSlash(url)
}
