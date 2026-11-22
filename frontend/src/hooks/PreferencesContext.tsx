import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

export type TextSize = 'normal' | 'large' | 'extra-large'
export type ContrastMode = 'standard' | 'high'

const STORAGE_KEY = 'scam_shield_prefs'

interface Prefs {
  textSize: TextSize
  contrast: ContrastMode
  readAloud: boolean
}

const defaults: Prefs = {
  textSize: 'normal',
  contrast: 'standard',
  readAloud: false,
}

function loadPrefs(): Prefs {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return defaults
    return { ...defaults, ...(JSON.parse(raw) as Partial<Prefs>) }
  } catch {
    return defaults
  }
}

function applyDom(prefs: Prefs) {
  document.documentElement.dataset.textSize = prefs.textSize
  if (prefs.contrast === 'high') {
    document.documentElement.dataset.contrast = 'high'
  } else {
    delete document.documentElement.dataset.contrast
  }
}

interface PreferencesContextValue extends Prefs {
  setTextSize: (v: TextSize) => void
  setContrast: (v: ContrastMode) => void
  setReadAloud: (v: boolean) => void
}

const PreferencesContext = createContext<PreferencesContextValue | null>(null)

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [prefs, setPrefs] = useState<Prefs>(() => {
    const p = loadPrefs()
    applyDom(p)
    return p
  })

  useEffect(() => {
    applyDom(prefs)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs))
  }, [prefs])

  const setTextSize = useCallback((textSize: TextSize) => {
    setPrefs((p) => ({ ...p, textSize }))
  }, [])

  const setContrast = useCallback((contrast: ContrastMode) => {
    setPrefs((p) => ({ ...p, contrast }))
  }, [])

  const setReadAloud = useCallback((readAloud: boolean) => {
    setPrefs((p) => ({ ...p, readAloud }))
  }, [])

  const value = useMemo(
    () => ({ ...prefs, setTextSize, setContrast, setReadAloud }),
    [prefs, setTextSize, setContrast, setReadAloud],
  )

  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>
}

export function usePreferences(): PreferencesContextValue {
  const ctx = useContext(PreferencesContext)
  if (!ctx) {
    throw new Error('usePreferences must be used within PreferencesProvider')
  }
  return ctx
}