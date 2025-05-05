# asi_process_management

## 📌 Descripción

Este módulo permite gestionar **procesos internos de una organización** en Odoo 16 Community, incluyendo actividades recurrentes asociadas a los mismos. Proporciona una estructura clara para documentar y planificar procesos como la nómina, planificación operativa, mantenimiento, entre otros.

## 🧩 Características

- Definición de **procesos internos** con departamento, objetivo y periodicidad.
- Registro de **actividades** asociadas a cada proceso.
- Gestión de **frecuencia** y tipo de recurrencia (diaria, semanal, mensual, etc.).
- Asignación de **responsables** (usuarios).
- Vista árbol y formulario para procesos y actividades.
- Datos de demostración incluidos.


## ⚙️ Instalación

1. Copia el módulo en tu carpeta de addons.
2. Reinicia el servidor Odoo.
3. Activa el modo desarrollador.
4. Instala el módulo desde **Aplicaciones**.

## 🧑‍💼 Modelos definidos

### `x.process`
- `name`: Nombre del proceso.
- `department_id`: Departamento responsable.
- `objective_header`: Objetivo principal.
- `objective_detail`: Objetivo detallado (HTML).
- `frequency`: Frecuencia (`daily`, `weekly`, `monthly`, `quarterly`).
- `recurrence_type`: Tipo de recurrencia.
- `user_ids`: Responsables del proceso.
- `activity_ids`: Actividades asociadas.

### `x.activity`
- `name`: Nombre de la actividad.
- `process_id`: Proceso al que pertenece.
- `duration`: Duración estimada en horas.
- `sequence`: Orden de ejecución.
- `description`: Descripción.

## 🔐 Seguridad

Los archivos `security.xml` y `ir.model.access.csv` otorgan acceso completo a los modelos para cualquier usuario.

> ⚠️ Es recomendable configurar grupos si se requiere control más granular.

## 🧪 Datos de prueba

Se incluye un proceso demo de "Gestión de Nómina" para el departamento de Recursos Humanos con un objetivo y descripción detallada.

## 🧱 Dependencias

- `base`
- `hr`
- `calendar`

## 🧑 Autor

Este módulo fue desarrollado por Javier Escobar para apoyar procesos organizacionales estructurados.

---


