/**
 * Analytics Client
 * 
 * v0
 */

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

  const buildVisitParameters = () => {
    const kwargs = {
      url: window.location.href,
      agent: navigator.userAgent,
      zone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      // time: Math.floor(Date.now() / 1000),
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

  return doRequest(`${config.host}${config.path}/${config.campaign}`, buildVisitParameters())
}
