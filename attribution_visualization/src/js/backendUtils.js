const apiAddress = window.location.hostname + ':80'

// Text attribution functions
export const fetchAttributions = async (textA, textB) => {
  try {
    const response = await fetch(`http://${apiAddress}/api/attribution`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text_a: textA,
        text_b: textB,
      }),
    })
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    throw new Error('Attribution fetch failed: ' + error.message)
  }
}

export const fetchWordTokens = async (textA, textB) => {
  try {
    const response = await fetch(`http://${apiAddress}/api/merge-words`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text_a: textA,
        text_b: textB,
      }),
    })
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    throw new Error('Word tokens fetch failed: ' + error.message)
  }
}

export const fetchWordcombinationTokens = async (textA, textB) => {
  try {
    const response = await fetch(`http://${apiAddress}/api/merge-word-combinations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text_a: textA,
        text_b: textB,
      }),
    })
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    throw new Error('Word combination tokens fetch failed: ' + error.message)
  }
}

export const fetchPos = async (textA, textB) => {
  try {
    const response = await fetch(`http://${apiAddress}/api/pos`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text_a: textA,
        text_b: textB,
      }),
    })
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    throw new Error('POS fetch failed: ' + error.message)
  }
}

export const fetchCombinationPos = async (textA, textB) => {
  try {
    const response = await fetch(`http://${apiAddress}/api/pos-combinations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text_a: textA,
        text_b: textB,
      }),
    })
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    throw new Error('POS combinations fetch failed: ' + error.message)
  }
}

// Image attribution functions
export const fetchImageAttribution = async (imageFile, caption = null) => {
  try {
    const formData = new FormData()
    formData.append('image', imageFile)
    if (caption) {
      formData.append('caption', caption)
    }

    const response = await fetch(`http://${apiAddress}/api/image-attribution-file`, {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    throw new Error('Image attribution fetch failed: ' + error.message)
  }
}

// Health check
export const checkHealth = async () => {
  try {
    const response = await fetch(`http://${apiAddress}/api/health`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    throw new Error('Health check failed: ' + error.message)
  }
}
