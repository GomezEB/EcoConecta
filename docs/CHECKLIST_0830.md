# Checklist de entrega — 21 noviembre 2026, 08:30 America/Bogota

## Alta prioridad
- [ ] Integrar `docs/BLOQUE_PARA_README.md` al `README.md`, reemplazando PENDIENTE por la URL real.
- [ ] Confirmar código final integrable en rama `main` y `git status` limpio.
- [ ] Frontend compila: `docker compose up --build -d` sin errores.
- [ ] Servicios locales sanos (`docker compose ps`), `/api/salud` devuelve `estado: ok`.
- [ ] Dos flujos completos demostrados sin cambiar de colectivo (opcional: `scripts/e2e_demo.py`).
- [ ] Probar 3 kg orgánicos = 6 puntos demo, nunca antes de cerrar la solicitud.
- [ ] Probar acceso denegado entre roles y preservación de PII.
- [ ] Servicio cloud accesible desde red externa, no solo localhost.
- [ ] Usuarios DEMO y datos ficticios cargados en **PostgreSQL cloud**.
- [ ] README incluye URL real, proveedor, instrucciones Docker, variables necesarias SIN secretos.
- [ ] Diagrama de arquitectura y modelo PostgreSQL compartidos.
- [ ] Presentación con problema, solución, usuarios, impacto, tecnologías, limitaciones.

## WhatsApp / IA
- [ ] Si se anuncia como funcional, verificar webhook HTTPS Meta, texto y mensaje de programación.
- [ ] Si se anuncia audio/imagen, verificar transcripción/clasificación y consentimiento.
- [ ] Marcar honestamente las funcionalidades condicionales; la IA no es requisito obligatorio.

## Seguridad / entrega
- [ ] `.env` y tokens nunca en GitHub.
- [ ] Datos ciudadanos de la demo son ficticios; no usar imágenes privadas.
- [ ] Entregar credenciales demo a jurados por canal privado.
- [ ] Probar desde celular la URL pública (no depender de tu portátil).
- [ ] Revisar límites/costos del proveedor y que el servicio no se duerma antes de la evaluación.
- [ ] Guardar alternativa: video corto del flujo probado (claramente identificado como respaldo).
