export type Person = {id: number; nombre: string; roles: string[]}
export type Citizen = {id: number; nombre: string; tipo_generador: string; habilitado_piloto: boolean}
export type RequestItem = {
  id: number; flujo: 'organicos' | 'reciclables'; estado: string;
  nombre: string; telefono: string; direccion: string; observaciones: string;
  preferencia_horaria: string; tipo_generador: string;
  recolector_id: number | null; coordinador_id: number | null;
  programada_para: string | null; cantidad_recibida: number | null; unidad: string | null;
}

const KEY = 'ecoconecta_token'
export const getToken = () => sessionStorage.getItem(KEY)
export const setToken = (token: string) => sessionStorage.setItem(KEY, token)
export const clearToken = () => sessionStorage.removeItem(KEY)

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (getToken()) headers.set('Authorization', `Bearer ${getToken()}`)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const res = await fetch(path, { ...options, headers })
  if (!res.ok) {
    let message = `Error HTTP ${res.status}`
    try { const body = await res.json(); message = typeof body.detail === 'string' ? body.detail : message } catch { /* no JSON */ }
    throw new Error(message)
  }
  return res.json() as Promise<T>
}

export const post = <T,>(path: string, payload?: unknown) => api<T>(path, { method: 'POST', body: payload ? JSON.stringify(payload) : undefined })
