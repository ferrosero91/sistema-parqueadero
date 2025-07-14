# Sistema de Gestión de Usuarios con Roles Personalizados

## 🎯 Descripción General

Se ha implementado un sistema completo de gestión de usuarios con roles personalizados y permisos por módulos para el sistema de administración de parqueaderos. El sistema permite crear, editar y eliminar usuarios, gestionar roles personalizados con permisos específicos, y controlar el acceso a diferentes módulos del sistema.

## 🏗️ Arquitectura del Sistema

### Modelos Implementados

#### 1. **Module** - Módulos del Sistema
- Define los módulos principales del sistema
- Cada módulo tiene permisos específicos
- Módulos por defecto: Dashboard, Gestión de Vehículos, Categorías, Reportes, etc.

#### 2. **Permission** - Permisos Específicos
- Permisos granulares dentro de cada módulo
- Ejemplos: `view_dashboard`, `vehicle_entry`, `manage_roles`, etc.
- Se pueden activar/desactivar individualmente

#### 3. **CustomRole** - Roles Personalizados
- Roles específicos por empresa (tenant)
- Roles del sistema: Administrador, Cajero, Operador, Visualizador
- Roles personalizados que se pueden crear según necesidades

#### 4. **RolePermission** - Relación Roles-Permisos
- Asigna permisos específicos a cada rol
- Permite configuración granular de permisos

#### 5. **UserRole** - Roles de Usuario
- Asigna múltiples roles a un usuario
- Rol principal para determinar permisos básicos
- Un usuario puede tener varios roles

#### 6. **UserPermission** - Permisos Específicos de Usuario
- Permite sobre-escritura de permisos por usuario
- Permisos específicos que anulan los del rol
- Control granular por usuario

#### 7. **AccessLog** - Bitácora de Acceso
- Registra todas las acciones del sistema
- Incluye: login, logout, cambios de permisos, etc.
- Auditoría completa del sistema

## 🔐 Funcionalidades Implementadas

### 1. **Gestión de Roles**
- ✅ Crear roles personalizados
- ✅ Editar roles existentes
- ✅ Asignar permisos a roles mediante checkboxes
- ✅ Activar/desactivar roles
- ✅ Eliminar roles (excepto roles del sistema)

### 2. **Gestión de Usuarios**
- ✅ Crear usuarios con roles específicos
- ✅ Asignar múltiples roles a un usuario
- ✅ Definir rol principal
- ✅ Permisos específicos por usuario (sobre-escritura)
- ✅ Activar/desactivar usuarios

### 3. **Sistema de Permisos**
- ✅ Permisos granulares por módulo
- ✅ Verificación de permisos en tiempo real
- ✅ Herencia de permisos por roles
- ✅ Sobre-escritura de permisos por usuario

### 4. **Vistas y Interfaces**
- ✅ Lista de roles con filtros
- ✅ Asignación de permisos a roles
- ✅ Vista general de permisos por usuario
- ✅ Bitácora de acceso y cambios
- ✅ Interfaz moderna con Tailwind CSS

## 📋 Módulos y Permisos por Defecto

### Dashboard
- `view_dashboard` - Ver panel principal

### Gestión de Vehículos
- `vehicle_entry` - Registrar entrada de vehículos
- `vehicle_exit` - Registrar salida de vehículos
- `print_tickets` - Imprimir tickets

### Categorías de Vehículos
- `view_categories` - Ver categorías
- `create_categories` - Crear categorías
- `edit_categories` - Editar categorías
- `delete_categories` - Eliminar categorías

### Reportes
- `view_reports` - Ver reportes
- `export_reports` - Exportar reportes

### Cuadre de Caja
- `open_shift` - Abrir turno de caja
- `close_shift` - Cerrar turno de caja
- `register_movements` - Registrar movimientos
- `view_cash_history` - Ver historial de caja

### Historial de Movimientos
- `view_movement_history` - Ver historial
- `export_movement_history` - Exportar historial

### Gestión de Usuarios
- `view_users` - Ver usuarios
- `create_users` - Crear usuarios
- `edit_users` - Editar usuarios
- `delete_users` - Eliminar usuarios
- `manage_roles` - Gestionar roles

### Configuración
- `view_settings` - Ver configuración
- `edit_settings` - Editar configuración

### Exportación de Datos
- `export_data` - Exportar datos

## 👥 Roles por Defecto

### 1. **Administrador**
- Acceso completo a todas las funcionalidades
- Puede gestionar usuarios, roles y permisos
- Control total del sistema

### 2. **Cajero**
- Gestión de entradas/salidas de vehículos
- Operaciones de caja (abrir/cerrar turnos)
- Ver reportes y exportar datos
- No puede gestionar usuarios

### 3. **Operador**
- Operaciones básicas del sistema
- Entradas/salidas de vehículos
- Ver reportes y categorías
- No puede gestionar usuarios ni caja

### 4. **Visualizador**
- Solo visualización de reportes
- Acceso al dashboard
- Sin permisos de modificación

## 🎨 Interfaz de Usuario

### Características del Diseño
- **Responsivo**: Adaptable a móviles y desktop
- **Moderno**: Diseño con Tailwind CSS
- **Intuitivo**: Navegación clara y fácil
- **Accesible**: Alto contraste y navegación por teclado

### Páginas Implementadas
1. **Lista de Roles** (`/roles/`)
   - Vista general de todos los roles
   - Filtros de búsqueda
   - Estadísticas de uso

2. **Gestión de Permisos** (`/roles/<id>/permisos/`)
   - Asignación de permisos mediante checkboxes
   - Agrupación por módulos
   - Contadores en tiempo real

3. **Vista General** (`/permisos/overview/`)
   - Matriz de permisos por usuario
   - Resumen por módulos
   - Acceso rápido a gestión

4. **Bitácora** (`/permisos/bitacora/`)
   - Registro de todas las acciones
   - Filtros por fecha, usuario y acción
   - Auditoría completa

## 🔧 Comandos de Gestión

### Inicialización del Sistema
```bash
python manage.py setup_roles_permissions
```

### Opciones del Comando
- `--tenant-id`: Inicializar solo para una empresa específica
- `--force`: Forzar recreación de módulos y permisos

## 🚀 URLs Implementadas

### Gestión de Roles
- `GET /roles/` - Lista de roles
- `GET /roles/crear/` - Crear nuevo rol
- `GET /roles/<id>/editar/` - Editar rol
- `GET /roles/<id>/permisos/` - Asignar permisos
- `POST /roles/<id>/eliminar/` - Eliminar rol
- `POST /roles/<id>/toggle-status/` - Activar/desactivar

### Gestión de Usuarios
- `GET /usuarios/<id>/roles/` - Asignar roles a usuario
- `GET /usuarios/<id>/permisos/` - Permisos específicos

### Vistas Generales
- `GET /permisos/overview/` - Vista general de permisos
- `GET /permisos/bitacora/` - Bitácora de acceso

## 🔒 Seguridad y Validación

### Decoradores de Seguridad
- `@permission_required('manage_roles')` - Solo usuarios con permiso
- `@tenant_required` - Verificación de empresa
- `@login_required` - Autenticación requerida

### Validaciones
- Verificación de permisos en tiempo real
- Validación de roles por empresa
- Control de acceso a módulos específicos

## 📊 Características Avanzadas

### 1. **Sobre-escritura de Permisos**
- Los permisos específicos de usuario anulan los del rol
- Control granular por usuario
- Flexibilidad máxima en asignación de permisos

### 2. **Múltiples Roles por Usuario**
- Un usuario puede tener varios roles
- Rol principal determina permisos básicos
- Combinación de permisos de múltiples roles

### 3. **Auditoría Completa**
- Registro de todas las acciones del sistema
- Bitácora de cambios de permisos
- Trazabilidad completa

### 4. **Interfaz Intuitiva**
- Checkboxes organizados por módulos
- Contadores en tiempo real
- Filtros y búsquedas avanzadas

## 🎯 Beneficios del Sistema

### Para Administradores
- Control granular de permisos
- Flexibilidad en asignación de roles
- Auditoría completa del sistema
- Interfaz intuitiva y moderna

### Para Usuarios
- Acceso controlado según necesidades
- Interfaz clara y fácil de usar
- Permisos específicos según función

### Para el Sistema
- Escalabilidad y mantenibilidad
- Seguridad mejorada
- Trazabilidad completa
- Flexibilidad en configuración

## 🔮 Próximas Mejoras

### Funcionalidades Opcionales
1. **Panel Visual Avanzado**
   - Gráficos de uso de permisos
   - Estadísticas detalladas
   - Dashboard de administración

2. **Permisos Temporales**
   - Permisos con fecha de expiración
   - Acceso temporal a módulos específicos

3. **Notificaciones**
   - Alertas de cambios de permisos
   - Notificaciones de acceso denegado

4. **API REST**
   - Endpoints para gestión programática
   - Integración con sistemas externos

## 📝 Conclusión

El sistema de gestión de usuarios con roles personalizados está completamente implementado y funcional. Proporciona:

- ✅ Control granular de permisos
- ✅ Interfaz moderna e intuitiva
- ✅ Auditoría completa
- ✅ Escalabilidad y flexibilidad
- ✅ Seguridad robusta

El sistema está listo para producción y puede ser utilizado inmediatamente para gestionar usuarios y permisos en el sistema de parqueaderos. 