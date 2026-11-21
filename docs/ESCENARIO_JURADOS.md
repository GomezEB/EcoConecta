# Guion de demostración para los jurados — EcoConecta

## Antes de iniciar
- Abrir URL **pública real** y verificar `/api/salud`.
- Ingresar como Fundación con cuenta DEMO, sin mostrar contraseña en pantalla compartida.
- Comprobar que el estado inicial incluye al menos una solicitud `organicos` de **unidad_productiva** y otra `reciclables` de **hogar**.
- Confirmar regla demo activa de 2 puntos/kg **NO oficial**.
- Tener cuentas de huertero y reciclador preparadas en otro navegador/perfil.

## Recorrido orgánicos
1. Mostrar solicitud de unidad productiva, identificador y estado inicial.
2. Ingresar como encargado huerta. Mostrar bandeja **solo de orgánicos**.
3. Revisar solicitud, asignar el recolector de huerta.
4. Elegir una fecha/hora **futuras** y confirmar programación.
5. Ingresar como encargado de huerta asignado y confirmar recolección **3 kg**.
6. Consultar la solicitud: estado `recolectada`, historial, cantidad y **6 puntos** (3 kg × 2), si la regla está activa.

## Recorrido reciclables
7. Ingresar como encargado reciclaje; mostrar **solo reciclables**, no orgánicos.
8. Revisar, asignar, programar, confirmar **2 kg**, comprobar **4 puntos**.
9. Mostrar el resumen Fundación y exportar CSV sin PII.

## Comunicación y educación
10. Mostrar educación ambiental desde web o WhatsApp.
11. Si Meta está conectada: enviar mensaje real, comprobar recepción y confirmación de programación. Si no, indicar honestamente que es un adaptador pendiente de credenciales.
12. Mostrar GitHub, README, arquitectura, PostgreSQL y Docker.

## Preguntas frecuentes
- **¿De dónde sale la puntuación?** Es parámetro demo; 2 puntos por kilogramo, con redondeo hacia abajo. FSD debe definir/validar los valores reales.
- **¿Por qué dos flujos?** Responsables operativos distintos y privacidad entre colectivos.
- **¿La IA decide la ruta o el horario?** No; los cambios críticos se confirman manualmente.
- **¿Dónde están las contraseñas?** Variables de entorno privadas en el proveedor. No en GitHub.
- **¿Qué limitaciones hay?** Webhook Meta y medios dependen de configuración, infraestructura gratuita tiene límites, migraciones versionadas están pendientes.
