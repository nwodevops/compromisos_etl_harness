# Estructura — arquetipo mínimo

```
mi_etl/
├── README.md
├── AGENTS.md
├── CHECKPOINTS.md
├── feature_list.json
├── init.sh
├── project-config.json
├── switch-env.sh
├── inputs.yaml
├── progress/
├── docs/
│   ├── arquitectura.md
│   ├── verification.md
│   └── harness/
├── .agents/skills/hop-python-etl/
├── h2/
├── metadata/
├── python/
│   ├── create_stg.py
│   ├── main.py
│   ├── io/leer_h2.py
│   └── io/escribir_excel.py
├── logica/demo.py
├── workflows/
│   ├── wf_create_stg.hwf
│   └── wf_main.hwf
├── pipelines/pl_demo.hpl
├── environments/
├── input_excel/
└── output/          (generado)
```

Nuevo proyecto: `./scripts/nuevo_etl.sh /ruta/mi_etl`  
Regenerar cascarón: `./scripts/sync_archetype.sh`
