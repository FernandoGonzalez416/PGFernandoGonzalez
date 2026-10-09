from enum import Enum


class Capacidad(str, Enum):
    PRODUCTOS_CONSULTAR = "productos:consultar"
    PRODUCTOS_EDITAR = "productos:editar"
    CATEGORIAS_GESTIONAR = "categorias:gestionar"
    PROVEEDORES_GESTIONAR = "proveedores:gestionar"
    STOCK_CONSULTAR = "stock:consultar"
    VENTAS_REGISTRAR = "ventas:registrar"
    VENTAS_ANULAR = "ventas:anular"
    INVENTARIO_AJUSTAR = "inventario:ajustar"
    INVENTARIO_VER_MOVIMIENTOS = "inventario:ver_movimientos"
    ALERTAS_VER = "alertas:ver"
    REPORTES_VER = "reportes:ver"
    PREDICCION_VER = "prediccion:ver"
    SUGERENCIAS_VER = "sugerencias:ver"
    SUGERENCIAS_ATENDER = "sugerencias:atender"
    USUARIOS_GESTIONAR = "usuarios:gestionar"
    CONFIGURACION_GESTIONAR = "configuracion:gestionar"


CAPACIDADES_POR_ROL: dict[Capacidad, frozenset[str]] = {
    Capacidad.PRODUCTOS_CONSULTAR: frozenset({"administrador", "propietario", "padre"}),
    Capacidad.PRODUCTOS_EDITAR: frozenset({"administrador", "propietario"}),
    Capacidad.CATEGORIAS_GESTIONAR: frozenset({"administrador", "propietario"}),
    Capacidad.PROVEEDORES_GESTIONAR: frozenset({"administrador", "propietario"}),
    Capacidad.STOCK_CONSULTAR: frozenset({"administrador", "propietario", "padre"}),
    Capacidad.VENTAS_REGISTRAR: frozenset({"administrador", "propietario", "padre"}),
    Capacidad.VENTAS_ANULAR: frozenset({"administrador", "propietario", "padre"}),
    Capacidad.INVENTARIO_AJUSTAR: frozenset({"administrador", "propietario"}),
    Capacidad.INVENTARIO_VER_MOVIMIENTOS: frozenset({"administrador", "propietario", "padre"}),
    Capacidad.ALERTAS_VER: frozenset({"administrador", "propietario", "padre"}),
    Capacidad.REPORTES_VER: frozenset({"administrador", "propietario"}),
    Capacidad.PREDICCION_VER: frozenset({"administrador"}),
    Capacidad.SUGERENCIAS_VER: frozenset({"administrador", "propietario", "padre"}),
    Capacidad.SUGERENCIAS_ATENDER: frozenset({"administrador", "propietario", "padre"}),
    Capacidad.USUARIOS_GESTIONAR: frozenset({"administrador"}),
    Capacidad.CONFIGURACION_GESTIONAR: frozenset({"administrador"}),
}


def capacidades_de_rol(rol: str) -> list[str]:
    """Capacidades que tiene un rol, derivadas de CAPACIDADES_POR_ROL.

    Única fuente de verdad: si un rol deja de tener una capacidad, la API y el
    frontend se enteran por esta misma función. El orden es estable
    (alfabético por valor) para que las respuestas sean deterministas y
    fáciles de comparar en las pruebas.
    """
    return sorted(
        capacidad.value
        for capacidad, roles in CAPACIDADES_POR_ROL.items()
        if rol in roles
    )


def verificar_anulacion_venta(venta_usuario_id: str, usuario_id: str, rol: str) -> None:
    """P14 fila 9: admin y dueño anulan cualquier venta; padre solo las de su propia sesión."""
    if rol == "padre" and venta_usuario_id != usuario_id:
        raise PermissionError(
            "El padre solo puede anular ventas registradas desde su propia sesión"
        )