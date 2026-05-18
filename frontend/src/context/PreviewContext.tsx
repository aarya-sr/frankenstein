import { createContext, useContext, useReducer, type Dispatch, type ReactNode } from "react"
import type { PreviewState } from "../types/preview"
import { initialPreviewState, previewReducer, type PreviewAction } from "./previewReducer"

const PreviewStateContext = createContext<PreviewState>(initialPreviewState)
const PreviewDispatchContext = createContext<Dispatch<PreviewAction>>(() => {})

export function PreviewProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(previewReducer, initialPreviewState)

  return (
    <PreviewStateContext.Provider value={state}>
      <PreviewDispatchContext.Provider value={dispatch}>
        {children}
      </PreviewDispatchContext.Provider>
    </PreviewStateContext.Provider>
  )
}

export function usePreviewState(): PreviewState {
  return useContext(PreviewStateContext)
}

export function usePreviewDispatch(): Dispatch<PreviewAction> {
  return useContext(PreviewDispatchContext)
}
