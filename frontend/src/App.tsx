import { FormEvent, useCallback, useEffect, useState } from 'react'
import { api, post, clearToken, getToken, setToken, type Person, type Citizen, type RequestItem } from './api'

type Me = {id: number; nombre: string; correo: string; roles: string[]}
type Summary = {total: number; por_flujo: Record<string, number>; por_estado: Record<string, number>; puntos: number}
const has = (me: Me | null, roles: string[]) => Boolean(me?.roles.some(r => roles.includes(r)))
const friendlyFlow = (flow: string) => flow === 'organicos' ? 'Orgánicos 🌱' : 'Reciclables ♻️'

function Login({onLogin}: {onLogin: () => void}) {
  const [email, setEmail] = useState('')
  const [pass, setPass] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const r = await post<{token: string}>('/api/auth/login', {correo: email, contrasena: pass})
      setToken(r.token); onLogin()
    } catch (err) { setError(err instanceof Error ? err.message : 'No fue posible ingresar') }
    finally { setBusy(false) }
  }
  return <main className="mx-auto flex min-h-screen max-w-lg items-center px-4 py-12">
    <div className="card w-full space-y-5">
      <div className="text-center"><span className="text-5xl">♻️</span><h1 className="text-3xl font-bold text-eco-900">EcoConecta</h1>
        <p className="text-sm text-slate-500">Villas de San Pablo · Panel de operación</p></div>
      <form onSubmit={submit} className="space-y-4">
        <div><label className="label">Correo del encargado</label><input className="input" type="email" required value={email} onChange={e=>setEmail(e.target.value)} /></div>
        <div><label className="label">Contraseña</label><input className="input" type="password" required value={pass} onChange={e=>setPass(e.target.value)} /></div>
        {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</p>}
        <button disabled={busy} className="btn-primary w-full">{busy ? 'Validando...' : 'Iniciar sesión'}</button>
      </form><p className="text-xs text-slate-500">Las personas de la comunidad solicitan la recolección desde WhatsApp. Las cuentas de este panel se crean administrativamente.</p>
    </div>
  </main>
}

function RequestCard({item, me, people, onUpdate}: {item: RequestItem; me: Me; people: Person[]; onUpdate: () => void}) {
  const coordRole = item.flujo === 'organicos' ? 'coordinador_huerta' : 'coordinador_reciclaje'
  const collRole = item.flujo === 'organicos' ? 'huertero' : 'reciclador'
  const coord = me.roles.includes('administrador') || me.roles.includes(coordRole)
  const collector = me.roles.includes(collRole) && item.recolector_id === me.id
  const [selection, setSelection] = useState(String(item.recolector_id || ''))
  const [schedule, setSchedule] = useState('')
  const [amount, setAmount] = useState('1')
  const [unit, setUnit] = useState('bolsas')
  const [busy, setBusy] = useState(false)
  const [feedback, setFeedback] = useState('')
  const eligible = people.filter(p => p.roles.includes(collRole))
  async function action(path: string, body?: unknown) {
    setBusy(true); setFeedback('')
    try {
      const result = await post<Record<string, unknown>>(`/api/solicitudes/${item.id}/${path}`, body)
      setFeedback(result.whatsapp_notificado === false && path === 'programar' ? 'Programada. Aviso WhatsApp pendiente de credenciales Meta.' : 'Operación guardada.')
      onUpdate()
    } catch (err) { setFeedback(err instanceof Error ? err.message : 'No se pudo actualizar') }
    finally { setBusy(false) }
  }
  return <article className="card space-y-3">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div><p className="eyebrow">Solicitud #{item.id} · {friendlyFlow(item.flujo)}</p><h3 className="text-lg font-bold">{item.nombre}</h3></div>
      <span className="rounded-full bg-eco-50 px-3 py-1 text-xs font-semibold text-eco-900">{item.estado.replaceAll('_',' ')}</span>
    </div>
    <div className="space-y-1 text-sm text-slate-700">
      <p><strong>Dirección:</strong> {item.direccion}</p><p><strong>Contacto:</strong> {item.telefono}</p>
      <p><strong>Tipo:</strong> {item.tipo_generador}</p><p><strong>Horario deseado:</strong> {item.preferencia_horaria || 'No indicado'}</p>
      {item.observaciones && <p><strong>Observaciones:</strong> {item.observaciones}</p>}
      {item.programada_para && <p><strong>Programada:</strong> {new Date(item.programada_para).toLocaleString('es-CO')}</p>}
      {item.cantidad_recibida != null && <p><strong>Recibido:</strong> {item.cantidad_recibida} {item.unidad}</p>}
    </div>
    {coord && item.estado === 'recibida' && <button disabled={busy} onClick={() => action('revisar')} className="btn-primary">Revisar solicitud</button>}
    {coord && ['recibida','en_revision'].includes(item.estado) && <div className="flex flex-wrap gap-2">
      <select className="input max-w-xs" value={selection} onChange={e => setSelection(e.target.value)} aria-label="Encargado">
        <option value="">Selecciona un encargado</option>
        {eligible.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
      </select><button disabled={busy || !selection} className="btn-primary" onClick={() => action('asignar', {recolector_id: Number(selection)})}>Asignar</button>
    </div>}
    {coord && item.estado === 'asignada' && <div className="flex flex-wrap gap-2">
      <input aria-label="Día y hora" className="input max-w-xs" type="datetime-local" value={schedule} onChange={e => setSchedule(e.target.value)} />
      <button className="btn-primary" disabled={busy || !schedule} onClick={() => action('programar', {fecha_hora: new Date(schedule).toISOString()})}>Confirmar programación</button>
    </div>}
    {collector && item.estado === 'programada' && <div className="flex flex-wrap gap-2">
      <input aria-label="Cantidad" className="input max-w-28" type="number" min="0" step="0.1" value={amount} onChange={e=>setAmount(e.target.value)} />
      <select aria-label="Unidad" className="input max-w-40" value={unit} onChange={e=>setUnit(e.target.value)}><option value="bolsas">Bolsas</option><option value="kg">kg</option><option value="unidades">Unidades</option></select>
      <button className="btn-primary" disabled={busy || !amount} onClick={()=>action('recolectar', {cantidad_recibida: Number(amount), unidad: unit})}>Confirmar recogida</button>
    </div>}
    {feedback && <p aria-live="polite" className="rounded-xl bg-slate-100 p-3 text-sm">{feedback}</p>}
  </article>
}

function Dashboard({me}: {me: Me}) {
  const [requests, setRequests] = useState<RequestItem[]>([])
  const [people, setPeople] = useState<Person[]>([])
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const canCoord = has(me, ['administrador', 'coordinador_huerta', 'coordinador_reciclaje'])
  const load = useCallback(async () => {
    try {
      const rs = await api<RequestItem[]>('/api/solicitudes'); setRequests(rs)
      if (canCoord) setPeople(await api<Person[]>('/api/personal'))
    } catch (err) { setMessage(err instanceof Error ? err.message : 'Error cargando solicitudes') }
  }, [canCoord])
  useEffect(() => { void load() }, [load])
  return <section className="space-y-4">
    <div className="flex flex-wrap items-center justify-between gap-2"><div><p className="eyebrow">Operación diaria</p><h2 className="text-2xl font-bold">Bandeja de solicitudes</h2></div>
      <button onClick={()=>{setBusy(true);void load().finally(()=>setBusy(false))}} disabled={busy} className="btn-secondary">Actualizar</button></div>
    {message && <p role="alert" className="rounded-xl bg-yellow-50 p-3 text-yellow-900">{message}</p>}
    {requests.length ? <div className="grid gap-4 lg:grid-cols-2">{requests.map(r=><RequestCard key={r.id} item={r} me={me} people={people} onUpdate={()=>void load()}/>)}</div> :
      <div className="card text-slate-600">Todavía no hay solicitudes disponibles en tu bandeja. La fundación puede cargar solicitudes de prueba; las reales llegarán desde WhatsApp.</div>}
  </section>
}

function Admin() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [citizens, setCitizens] = useState<Citizen[]>([])
  const [phone, setPhone] = useState('573001234567')
  const [name, setName] = useState('Vecino de prueba')
  const [address, setAddress] = useState('Villas de San Pablo, Manzana 4, Casa 12')
  const [generator, setGenerator] = useState('hogar')
  const [citizenId, setCitizenId] = useState('')
  const [flow, setFlow] = useState('organicos')
  const [preference, setPreference] = useState('Mañana en la tarde')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [rule, setRule] = useState('1')
  const [ruleName, setRuleName] = useState('Regla provisional DEMO; pendiente validación FSD')
  const load = async () => {
    try { setSummary(await api<Summary>('/api/admin/resumen')); setCitizens(await api<Citizen[]>('/api/ciudadanos')) }
    catch (err) { setError(err instanceof Error ? err.message : 'Error') }
  }
  useEffect(() => { void load() }, [])
  async function createCitizen(e: FormEvent) {
    e.preventDefault(); setError('');setSuccess('')
    try { const p = await post<{id: number}>('/api/ciudadanos', {telefono:phone, nombre:name, direccion:address, tipo_generador:generator, consentimiento:true, habilitado_piloto:true});
      setCitizenId(String(p.id));setSuccess(`Ciudadano de demostración #${p.id} creado`);await load() }
    catch(err){setError(err instanceof Error?err.message:'Error')}
  }
  async function createRequest(e: FormEvent) {
    e.preventDefault();setError('');setSuccess('')
    try {const p=await post<{id:number}>('/api/solicitudes',{ciudadano_id:Number(citizenId),flujo,preferencia_horaria:preference,observaciones:'Prueba desde panel administrativo'});
      setSuccess(`Solicitud de prueba #${p.id} registrada. Ve a Bandeja.`);await load()}
    catch(err){setError(err instanceof Error?err.message:'Error')}
  }
  async function setRule(e:FormEvent){e.preventDefault();setError('');setSuccess('');
    try {await api('/api/admin/regla-puntos',{method:'PUT',body:JSON.stringify({puntos_por_solicitud:Number(rule),nombre:ruleName})});setSuccess('Regla demostrativa actualizada')}
    catch(err){setError(err instanceof Error?err.message:'Error')}
  }
  async function csvDownload(){
    try {const token=getToken();const res=await fetch('/api/admin/exportar-csv',{headers:{Authorization:`Bearer ${token}`}}); if(!res.ok) throw new Error('No se pudo exportar');
      const blob=await res.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='ecoconecta_reporte.csv';a.click();URL.revokeObjectURL(url)}
    catch(err){setError(err instanceof Error?err.message:'Error')}
  }
  return <section className="space-y-5">
    <div><p className="eyebrow">Fundación Santo Domingo</p><h2 className="text-2xl font-bold">Estadísticas y demostración</h2></div>
    {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-red-800">{error}</p>}
    {success && <p aria-live="polite" className="rounded-xl bg-eco-50 p-3 text-eco-900">{success}</p>}
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {[['Solicitudes',summary?.total],['Orgánicos',summary?.por_flujo?.organicos || 0],['Reciclables',summary?.por_flujo?.reciclables || 0],['Puntos (piloto)',summary?.puntos]].map(([label,value])=>
        <div className="card" key={String(label)}><p className="text-sm text-slate-500">{label}</p><strong className="text-3xl text-eco-900">{value??'—'}</strong></div>)}
    </div>
    <div className="grid gap-4 lg:grid-cols-2">
      <form onSubmit={createCitizen} className="card space-y-3"><h3 className="text-lg font-bold">1. Ciudadano de prueba</h3>
        <p className="text-sm text-slate-500">Utiliza información ficticia; no envía datos a WhatsApp.</p>
        <div><label className="label">Nombre</label><input className="input" value={name} onChange={e=>setName(e.target.value)} required/></div>
        <div><label className="label">Teléfono ficticio</label><input className="input" value={phone} onChange={e=>setPhone(e.target.value)} required/></div>
        <div><label className="label">Dirección</label><input className="input" value={address} onChange={e=>setAddress(e.target.value)} required/></div>
        <div><label className="label">Tipo de generador</label><select className="input" value={generator} onChange={e=>setGenerator(e.target.value)}><option value="hogar">Hogar</option><option value="unidad_productiva">Unidad productiva</option></select></div>
        <button className="btn-primary">Crear ciudadano de prueba</button>
      </form>
      <form onSubmit={createRequest} className="card space-y-3"><h3 className="text-lg font-bold">2. Crear solicitud de prueba</h3>
        <div><label className="label">Ciudadano habilitado</label><select className="input" value={citizenId} onChange={e=>setCitizenId(e.target.value)} required><option value="">Selecciona una cuenta</option>{citizens.filter(c=>c.habilitado_piloto).map(c=><option key={c.id} value={c.id}>{c.nombre} (#{c.id})</option>)}</select></div>
        <div><label className="label">Flujo</label><select className="input" value={flow} onChange={e=>setFlow(e.target.value)}><option value="organicos">Orgánicos</option><option value="reciclables">Reciclables</option></select></div>
        <div><label className="label">Horario preferido</label><input className="input" required value={preference} onChange={e=>setPreference(e.target.value)} /></div>
        <button className="btn-primary">Crear solicitud</button>
      </form>
      <form onSubmit={setRule} className="card space-y-3"><h3 className="text-lg font-bold">Regla de puntos — DEMO</h3>
        <p className="text-sm text-amber-800">No es un valor oficial de Fundación Santo Domingo. Solo se otorgan puntos después de la recolección.</p>
        <div><label className="label">Puntos por recolección completada</label><input className="input" type="number" min="0" max="10000" value={rule} onChange={e=>setRule(e.target.value)} /></div>
        <div><label className="label">Nombre de la regla</label><input className="input" value={ruleName} onChange={e=>setRuleName(e.target.value)} /></div>
        <button className="btn-secondary">Guardar regla de demostración</button>
      </form>
      <div className="card space-y-3"><h3 className="text-lg font-bold">Reportes de impacto</h3><p className="text-sm text-slate-600">Exportación agregada por solicitud sin nombre, teléfono o dirección.</p><button className="btn-primary" onClick={csvDownload}>Descargar CSV</button>
      <p className="text-sm text-slate-500">Estados: {Object.entries(summary?.por_estado || {}).map(([k,v])=>`${k}: ${v}`).join(' · ') || 'sin registros'}</p></div>
    </div>
  </section>
}

function Education(){
  const [tips,setTips]=useState<{titulo:string;detalle:string}[]>([])
  useEffect(()=>{void api<{consejos:{titulo:string;detalle:string}[]}>('/api/educacion').then(d=>setTips(d.consejos))},[])
  return <section className="space-y-4"><div><p className="eyebrow">Información ambiental</p><h2 className="text-2xl font-bold">Guía para la comunidad</h2></div>
    <div className="grid gap-4 md:grid-cols-3">{tips.map(t=><div key={t.titulo} className="card"><h3 className="mb-2 font-bold text-eco-900">{t.titulo}</h3><p className="text-sm text-slate-600">{t.detalle}</p></div>)}</div></section>
}

export default function App() {
  const [me,setMe]=useState<Me|null>(null)
  const [tab,setTab]=useState<'bandeja'|'educacion'|'admin'>('bandeja')
  const [loading,setLoading]=useState(Boolean(getToken()))
  const reload = useCallback(()=>{
    setLoading(true);void api<Me>('/api/auth/me').then(setMe).catch(()=>{clearToken();setMe(null)}).finally(()=>setLoading(false))
  },[])
  useEffect(()=>{if(getToken())reload()},[reload])
  if(loading) return <p className="p-8">Cargando EcoConecta...</p>
  if(!me) return <Login onLogin={reload}/>
  const admin = me.roles.includes('administrador')
  return <div className="min-h-screen bg-slate-50">
    <header className="border-b border-slate-200 bg-white"><div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4">
      <div><div className="text-xl font-extrabold text-eco-900">♻️ EcoConecta</div><p className="text-xs text-slate-500">Villas de San Pablo · Operación comunitaria</p></div>
      <div className="flex items-center gap-3"><p className="max-w-48 truncate text-sm">{me.nombre}</p><button className="btn-secondary" onClick={()=>{clearToken();setMe(null)}}>Salir</button></div>
    </div></header>
    <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
      <nav className="flex flex-wrap gap-2" aria-label="Secciones">
        <button className={tab==='bandeja'?'btn-primary':'btn-secondary'} onClick={()=>setTab('bandeja')}>Solicitudes</button>
        <button className={tab==='educacion'?'btn-primary':'btn-secondary'} onClick={()=>setTab('educacion')}>Educación ambiental</button>
        {admin && <button className={tab==='admin'?'btn-primary':'btn-secondary'} onClick={()=>setTab('admin')}>Fundación / Demo</button>}
      </nav>
      {tab==='bandeja'?<Dashboard me={me}/>:tab==='educacion'?<Education/>:admin?<Admin/>:<Dashboard me={me}/>}
    </main>
    <footer className="mx-auto max-w-6xl px-4 py-6 text-xs text-slate-500">MVP oficial EcoConecta · Datos de prueba para la hackathon · Operaciones críticas bajo control humano.</footer>
  </div>
}
