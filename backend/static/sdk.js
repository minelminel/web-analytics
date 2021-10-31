/**
 * Analytics Client
 * 
 * v0
 */

const buildVisitParameters = () => {
  const kwargs = {
    // Full url
    url: window.location.href,
    // User agent string
    agent: navigator.userAgent,
    // Browser timezone
    zone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    // Epoch milliseconds
    time: Date.now(),
    // Screen resolution
    screen: `${window.screen.width}x${window.screen.height}`,
  }
  return kwargs
}

const doRequest = async (url, kwargs) => {
  const params = new URLSearchParams(kwargs)
  try {
    const response = await fetch(`${url}?${params.toString()}`, {
      method: "POST"
    })
    const data = await response.json()
    console.debug(data)
    return data
  } catch (error) {
    console.error(error)
    return error
  }
}

const analytics = (overrides = {}) => {
  const defaults = {
    host: "http://ec2-3-142-255-1.us-east-2.compute.amazonaws.com/",
    path: "/api/campaign",
    campaign: null
  }
  const config = {...defaults, ...overrides}
  if (config.campaign === null) {
    console.error(`Must provide campaign id`)
    return
  }
  return doRequest(`${config.host}${config.path}/${config.campaign}`, buildVisitParameters())
}
