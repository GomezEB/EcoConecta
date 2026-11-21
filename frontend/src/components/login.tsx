
import { useState, type FormEvent } from "react";
import { post, setToken } from "../api";

type LoginProps = {
  onLogin: () => void;
};

export default function Login({ onLogin }: LoginProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (busy) return;

    setBusy(true);
    setError("");

    try {
      const response = await post<{ token: string }>(
        "/api/auth/login",
        {
          correo: email.trim(),
          contrasena: password,
        }
      );

      if (!response.token) {
        throw new Error("No se recibió una sesión válida.");
      }

      setToken(response.token);
      onLogin();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "No se pudo iniciar sesión."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main
      className="flex min-h-screen items-center justify-center bg-[#F2F5F2] bg-cover bg-center bg-no-repeat px-4 py-8"
      style={{
        backgroundImage:
          "linear-gradient(rgba(6,59,46,0.20), rgba(6,59,46,0.30)), url('/fondo.png')",
      }}
    >
      <section className="grid w-full max-w-5xl overflow-hidden rounded-2xl bg-white shadow-2xl md:grid-cols-2">

        {/* PANEL IZQUIERDO */}
        <div className="relative flex min-h-[570px] flex-col justify-between overflow-hidden bg-[#063B2E] px-8 pb-10 pt-8 text-white sm:px-12">

          <div className="relative z-10">
            {/* LOGO OFICIAL */}
            <div className="">
              <img
                src="/logo-ecoconecta.png"
                alt="EcoConecta Villas de San Pablo"
                className="mx-auto h-auto w-full object-contain"
              />
            </div>

            <p className="mt-7 text-base leading-relaxed">
              Conectamos comunidad, recicladores y huerteros
              para gestionar solicitudes de recolección y
              fortalecer una cultura ambiental sostenible.
            </p>

            <div className="mt-7 flex flex-wrap gap-4">
              <span className="rounded-full border border-white/50 px-4 py-2 text-sm font-semibold">
                🌱 Orgánicos
              </span>

              <span className="rounded-full border border-white/50 px-4 py-2 text-sm font-semibold">
                ♻️ Reciclables
              </span>
            </div>
          </div>

          {/* PAISAJE DECORATIVO */}
          <svg
            className="pointer-events-none absolute bottom-0 left-0 w-full"
            viewBox="0 0 520 150"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M0 100 Q105 48 210 100 Q350 25 520 105 V150 H0Z"
              fill="#246B41"
            />
            <path
              d="M0 123 Q140 75 260 123 Q395 75 520 119 V150 H0Z"
              fill="#145535"
            />
            <path
              d="M0 139 Q130 115 250 137 Q380 105 520 137 V150 H0Z"
              fill="#0B472F"
            />

            <g fill="#78A978" opacity="0.75">
              <path d="M320 96 L347 76 L374 96 V124 H320Z" />
              <path d="M385 85 L419 63 L453 85 V125 H385Z" />
              <path d="M341 108 H351 V125 H341Z" fill="#063B2E" />
              <path d="M411 107 H422 V125 H411Z" fill="#063B2E" />
              <rect x="330" y="96" width="9" height="9" fill="#063B2E" />
              <rect x="355" y="96" width="9" height="9" fill="#063B2E" />
              <rect x="396" y="88" width="10" height="10" fill="#063B2E" />
              <rect x="431" y="88" width="10" height="10" fill="#063B2E" />
            </g>

            <g
              stroke="#86B783"
              strokeWidth="3"
              strokeLinecap="round"
            >
              <path d="M68 125 V94" />
              <path d="M68 105 Q43 103 46 86 Q65 89 68 105" />
              <path d="M68 100 Q89 78 101 83 Q97 100 68 100" />
            </g>
          </svg>

          <p className="relative z-10 mt-16 text-sm text-[#E0F2E5]">
            Tecnología para transformar nuestra comunidad.
          </p>
        </div>

        {/* PANEL DERECHO */}
        <div className="flex flex-col justify-center px-7 py-10 sm:px-12">
          <div className="mb-8">
            <p className="mb-3 text-sm font-bold text-[#168A2E]">
              PANEL DE OPERACIÓN
            </p>

            <h1 className="text-3xl font-extrabold text-[#063B2E]">
              Bienvenido de nuevo
            </h1>

            <p className="mt-4 text-sm leading-relaxed text-gray-600">
              Ingresa tus credenciales para gestionar las
              solicitudes de recolección.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label
                htmlFor="login-email"
                className="mb-2 block text-sm font-bold text-[#063B2E]"
              >
                Correo electrónico
              </label>

              <input
                id="login-email"
                type="email"
                required
                autoComplete="username"
                placeholder="correo@ejemplo.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-[#202522] outline-none focus:border-[#168A2E] focus:ring-2 focus:ring-[#168A2E]/20"
              />
            </div>

            <div>
              <label
                htmlFor="login-password"
                className="mb-2 block text-sm font-bold text-[#063B2E]"
              >
                Contraseña
              </label>

              <div className="relative">
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  placeholder="Ingresa tu contraseña"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 pr-24 text-[#202522] outline-none focus:border-[#168A2E] focus:ring-2 focus:ring-[#168A2E]/20"
                />

                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 rounded px-2 py-2 text-sm font-medium text-[#168A2E] underline"
                  aria-label={
                    showPassword
                      ? "Ocultar contraseña"
                      : "Mostrar contraseña"
                  }
                >
                  {showPassword ? "Ocultar" : "Mostrar"}
                </button>
              </div>
            </div>

            {error && (
              <p
                role="alert"
                className="rounded-xl bg-red-50 p-3 text-sm text-red-700"
              >
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-xl bg-[#168A2E] px-5 py-3.5 text-lg font-bold text-white transition hover:bg-[#106D25] focus:ring-2 focus:ring-[#063B2E] focus:ring-offset-2 disabled:opacity-60"
            >
              {busy ? "Iniciando sesión..." : "Iniciar sesión"}
            </button>
          </form>

          <div className="mt-8 border-t border-gray-200 pt-5">
            <p className="text-center text-sm leading-relaxed text-gray-500">
              Acceso exclusivo para huerteros, recicladores
              y personal autorizado de la Fundación.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
