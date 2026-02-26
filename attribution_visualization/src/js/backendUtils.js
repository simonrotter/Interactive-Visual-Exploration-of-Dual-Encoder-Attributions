const getApiBase = () => {
  if (window.location.port === '8020') {
    return '' // same origin, use relative URLs
  }
  return `http://${window.location.hostname}:8020`
}

const apiBase = getApiBase()
//fetch functions
export const fetchTexts = async () => {
  try {
    const response = await fetch(`${apiBase}/api/getTexts`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    throw new Error('Suche fehlgeschlagen: ' + error.message)
  }
}

export const fetchAttributions = async (id) => {
  try {
    const response = await fetch(`${apiBase}/api/getAttribution/${id}`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    throw new Error('Suche fehlgeschlagen: ' + error.message)
  }
}

export const fetchWordTokens = async (id) => {
  try {
    const response = await fetch(`${apiBase}/api/merge-words/${id}`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    throw new Error('Suche fehlgeschlagen: ' + error.message)
  }
}

export const fetchWordcombinationTokens = async (id) => {
  try {
    const response = await fetch(`${apiBase}/api/merge-word-combinations/${id}`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    throw new Error('Suche fehlgeschlagen: ' + error.message)
  }
}

export const fetchPos = async (id) => {
  try {
    const response = await fetch(`${apiBase}/api/pos/${id}`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    throw new Error('Suche fehlgeschlagen: ' + error.message)
  }
}

export const fetchCombinationPos = async (id) => {
  try {
    const response = await fetch(`${apiBase}/api/pos-combinations/${id}`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    throw new Error('Suche fehlgeschlagen: ' + error.message)
  }
}

export const fetchLengthStats = async () => {
  try {
    const response = await fetch(`${apiBase}/api/attribution-length-stats`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    throw new Error('Suche fehlgeschlagen: ' + error.message)
  }
}
