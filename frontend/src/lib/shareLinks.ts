export function smsLink(body: string, phone?: string): string {
  const text = encodeURIComponent(body)
  if (phone) {
    return `sms:${phone}?body=${text}`
  }
  return `sms:?body=${text}`
}

export function whatsAppLink(body: string): string {
  return `https://wa.me/?text=${encodeURIComponent(body)}`
}