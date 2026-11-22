import { useCallback } from 'react'

const MAX_PX = 1600

export function useImageDownscale() {
  const downscaleToJpeg = useCallback((file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const img = new Image()
      const url = URL.createObjectURL(file)
      img.onload = () => {
        URL.revokeObjectURL(url)
        let { width, height } = img
        if (width > MAX_PX || height > MAX_PX) {
          if (width >= height) {
            height = Math.round((height * MAX_PX) / width)
            width = MAX_PX
          } else {
            width = Math.round((width * MAX_PX) / height)
            height = MAX_PX
          }
        }
        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')
        if (!ctx) {
          reject(new Error('Could not process image'))
          return
        }
        ctx.drawImage(img, 0, 0, width, height)
        const dataUrl = canvas.toDataURL('image/jpeg', 0.85)
        const base64 = dataUrl.replace(/^data:image\/jpeg;base64,/, '')
        resolve(base64)
      }
      img.onerror = () => {
        URL.revokeObjectURL(url)
        reject(new Error('Could not load image'))
      }
      img.src = url
    })
  }, [])

  return { downscaleToJpeg }
}