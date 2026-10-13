---
name: release-etl
description: >-
  Corta la rama release solo con el ETL de medidas, sin arnés, agente ni
  skills. Usar cuando el usuario pida la rama release, cortar release, o
  publicar el ETL sin feature_list, progress, AGENTS.md ni .agents.
---

# Rama release solo con el ETL

`master` guarda el arnés, `AGENTS.md` y `.agents/skills/`. `release` es la foto que corre Windows con `init.bat remote` o `workflows/wf_main_windows.hwf`.

No se hace merge de `master` a `release`. Ese merge vuelve a traer `progress/`, `feature_list.json` y los skills. Cada corte se reconstruye desde `HEAD` de `master` con [`cortar_release.sh`](cortar_release.sh). El script y esta skill se quedan en `master`.

```bash
.agents/skills/release-etl/cortar_release.sh
```

El script exige el árbol de `master` limpio, arma un commit huérfano (sin historial del arnés) y mueve la rama `release` a ese commit. No hace push.

## Qué sale

- Arnés: `feature_list.json`, `CHECKPOINTS.md`, `progress/`, `docs/harness/`, `docs/verification.md`
- Agente y skills: `AGENTS.md`, `.agents/`
- Notas que no ejecutan nada: `ESTRUCTURA.md`, `input/notas.txt`, `python/plantilla_logica.py`, `pipelines/pl_demo.hpl`

## Qué se queda

- `python/` de la corrida y `logica/medidas.py` (sin `python/plantilla_logica.py`)
- `inputs.yaml`, `input/fuentes_medidas.json`
- `h2/`, `metadata/`, `workflows/wf_main.hwf`, `workflows/wf_main_windows.hwf`, `workflows/wf_create_stg.hwf`
- `environments/`, `switch-env.sh`, `switch-env.ps1`
- `scripts/step_*.bat`, `scripts/_py.bat`, `scripts/get_var.ps1`, `run_wf_main.bat`
- `init.sh`, `init.bat`
- `README.md`, `docs/arquitectura.md`, `.gitignore`, `logs/.gitkeep`

`client_secret.json`, `docs/credenciales/` y `project-config.json` siguen fuera de git. En la máquina remote se copian aparte.

## Cambio de código solo en release

`init.sh` e `init.bat` en `master` validan `feature_list.json`. En `release` ese archivo no existe. El script quita ese chequeo en las copias de la rama. El resto de `init` (switch-env, H2, las tres cargas, `main.py`, `verificar.py`, log en `logs/`) se conserva.
