# Handoff

Handoff de rollout, escrito desde `agent-rules` el 2026-08-20. No continúa
ninguna sesión de este repo: no tiene `From:` ni un `Next:` que apunte a
`sessions/`. Se borra en el primer commit de la sesión que lo lea, como
cualquier handoff (`rules/project-docs.md` § *HANDOFF.md*).

**`Next:`** migrar el `PENDING.md` de este repo al par `PENDING.md` +
`BACKLOG.md`, antes de que cualquier sesión vuelva a editar `PENDING.md`.

Si abriste este repo para otra cosa y no vas a tocar `PENDING.md`, no es tuyo:
dejá el archivo donde está y seguí con lo tuyo.

**Load**: `~/.claude/rules/project-docs.md` § *PENDING.md* y § *BACKLOG.md* — la
fuente canónica, que esta consigna no reemplaza.

## Por qué

`PENDING.md` era un archivo que hacía dos trabajos: el índice que escanea una
persona para decidir qué sigue, y el detalle desde el que trabaja un agente. Los
dos textos no son el mismo, y un archivo que intenta ser los dos deja de ser
escaneable mucho antes de dejar de ser útil. Desde el 2026-08-19 son dos
archivos apareados por id, y `pending-lint.py` los chequea juntos.

Este repo tiene el lint cableado pero nunca escribió su `BACKLOG.md`, así que
hoy el chequeo de pareo se saltea y nada falla. Eso es lo que cierra esta
sesión.

## El cableado, primero

El lint vendido acá quedó viejo el 2026-08-20, cuando se agregó la sección
`## Notas`. Una copia vieja rechaza un bullet de `## Notas` por no tener id, y
el error se lee como "ponele el id" en vez de "tu lint es viejo".

Ya fue re-cableado por el commit que trajo este archivo. Verificá que quedó bien
antes de empezar:

    bash ~/repos/agent-rules/scripts/pending-wire.sh --check

Tu repo no tiene que aparecer en la salida. Si aparece, corré:

    bash ~/repos/agent-rules/scripts/pending-wire.sh $(git rev-parse --show-toplevel)

## La migración

Un ítem vive en los dos archivos:

- **El bullet**, en `PENDING.md`, en español. Abre con `**[NNN]**` — tres dígitos
  al azar de 001-999, ancho fijo, para que el ojo baje por la columna — y dice
  qué es en una cláusula, máximo 140 caracteres con el id incluido. Sin paths,
  sin fechas, sin checkboxes, máximo un nivel de anidado.
- **La entrada**, en `BACKLOG.md`, en inglés, bajo `## NNN - slug`, plana: la
  prioridad y la sección viven en `PENDING.md` y repetirlas acá es un segundo
  lugar donde desincronizarse. Ahí va todo el detalle: qué cambia, por qué, qué
  se probó, qué archivos toca. Cierra con `Sessions:` y los slugs de `sessions/`
  que le correspondan, nunca paths.
- **La entrada se escribe antes que el bullet.** Al revés, el resumen se escribe
  contra nada y el detalle se reconstruye después de memoria.

Los ids se eligen al azar, nunca contando hacia arriba: "el próximo número
libre" obliga a leer el archivo para encontrar el máximo, y esa lectura es la
carrera entre dos sesiones. El lint falla si hay colisión.

### Tres reglas que se rompen solas si no las tenés a mano

1. **Nada se pierde.** Esto no es un recorte: cada párrafo que hoy está en
   `PENDING.md` se mueve a la entrada de su ítem. Si un ítem no tiene detalle,
   su entrada es una línea, y está bien.
2. **`## Notas` es la única sección que no aparea, y va primera.** Ahí va lo que
   el lector necesita para leer el resto y que no es de ningún ítem: un
   vencimiento que puso otro, una fecha de entrega, una instrucción para Pablo
   que no es una tarea. Sus bullets no llevan id ni entrada; el cap de 140 y el
   límite de anidado siguen aplicando. **No es un cajón**: si algo tiene dueño,
   es un ítem con id. Si el repo no tiene nada de esa forma, la sección no va.
3. **Reestructurar es gratis, cerrar no.** Podés partir secciones, reordenar por
   prioridad y reescribir bullets sin pedir permiso. Borrás un ítem sólo si vos
   mismo verificaste que está hecho, y lo decís en el recap. Lo que sólo puede
   confirmar Pablo se queda, nombrando el chequeo.

### Lo que no se crea

`QUEUE.md` no se crea acá. Es para trabajo que se despacha a otra sesión, a un
worktree o a una corrida desatendida, y un doc placeholder vacío entrena a los
agentes a ignorar el archivo. Se crea cuando haya algo que despachar.

### `AGENTS.md`

Si su mapa de estructura nombra `PENDING.md`, sumá `BACKLOG.md` al lado, con una
línea de qué guarda cada uno. Actualizá también su `## Last Agent`.

## El criterio de salida

Un comando, no una impresión:

    python3 scripts/pending-lint.py .

Tiene que salir 0, y el marcador de `PENDING.md` tiene que quedar en
`<!-- pending-lint: over140=0 deep=0 -->`. Si sale con un baseline mayor a 0,
quedó detalle en el índice: movelo a `BACKLOG.md` en vez de subir el baseline.

**In flight**: nada. El commit que trajo este archivo tocó sólo el lint vendido,
el hook y este handoff.

## El commit

`PENDING.md`, `BACKLOG.md`, `AGENTS.md`, el borrado de este archivo y lo que
haya tocado el cableado, todo junto, en un commit, con mensaje en inglés.
Recapitulá en español qué ítems quedaron, cuáles borraste y por qué, y cuáles
esperan un chequeo de Pablo.
