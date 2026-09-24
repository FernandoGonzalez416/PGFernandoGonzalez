import pytest

from app.core.capacidades import (
    Capacidad,
    CAPACIDADES_POR_ROL,
    verificar_anulacion_venta,
)


class TestCapacidadesEnum:
    def test_todas_las_capacidades_estan_definidas(self):
        expected = {
            "productos:consultar",
            "productos:editar",
            "categorias:gestionar",
            "proveedores:gestionar",
            "stock:consultar",
            "ventas:registrar",
            "ventas:anular",
            "inventario:ajustar",
            "inventario:ver_movimientos",
            "alertas:ver",
            "reportes:ver",
            "prediccion:ver",
            "sugerencias:ver",
            "sugerencias:atender",
            "usuarios:gestionar",
            "configuracion:gestionar",
        }
        actual = {c.value for c in Capacidad}
        assert actual == expected, f"Faltantes: {expected - actual}"


class TestCapacidadesPorRol:
    def test_capacidades_por_rol_estructura(self):
        for capacidad, roles in CAPACIDADES_POR_ROL.items():
            assert isinstance(roles, frozenset), f"{capacidad} no es frozenset"
            assert len(roles) > 0, f"{capacidad} está vacía"

    def test_productos_consultar_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.PRODUCTOS_CONSULTAR] == frozenset(
            {"administrador", "propietario", "padre"}
        )

    def test_productos_editar_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.PRODUCTOS_EDITAR] == frozenset(
            {"administrador", "propietario"}
        )

    def test_categorias_gestionar_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.CATEGORIAS_GESTIONAR] == frozenset(
            {"administrador", "propietario"}
        )

    def test_proveedores_gestionar_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.PROVEEDORES_GESTIONAR] == frozenset(
            {"administrador", "propietario"}
        )

    def test_stock_consultar_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.STOCK_CONSULTAR] == frozenset(
            {"administrador", "propietario", "padre"}
        )

    def test_ventas_registrar_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.VENTAS_REGISTRAR] == frozenset(
            {"administrador", "propietario", "padre"}
        )

    def test_ventas_anular_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.VENTAS_ANULAR] == frozenset(
            {"administrador", "propietario", "padre"}
        )

    def test_inventario_ajustar_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.INVENTARIO_AJUSTAR] == frozenset(
            {"administrador", "propietario"}
        )

    def test_inventario_ver_movimientos_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.INVENTARIO_VER_MOVIMIENTOS] == frozenset(
            {"administrador", "propietario", "padre"}
        )

    def test_alertas_ver_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.ALERTAS_VER] == frozenset(
            {"administrador", "propietario", "padre"}
        )

    def test_reportes_ver_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.REPORTES_VER] == frozenset(
            {"administrador", "propietario"}
        )

    def test_prediccion_ver_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.PREDICCION_VER] == frozenset({"administrador"})

    def test_sugerencias_ver_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.SUGERENCIAS_VER] == frozenset(
            {"administrador", "propietario", "padre"}
        )

    def test_sugerencias_atender_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.SUGERENCIAS_ATENDER] == frozenset(
            {"administrador", "propietario", "padre"}
        )

    def test_usuarios_gestionar_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.USUARIOS_GESTIONAR] == frozenset(
            {"administrador"}
        )

    def test_configuracion_gestionar_roles(self):
        assert CAPACIDADES_POR_ROL[Capacidad.CONFIGURACION_GESTIONAR] == frozenset(
            {"administrador"}
        )


class TestVerificarAnulacionVenta:
    def test_padre_proprio_pasa(self):
        try:
            verificar_anulacion_venta("usuario123", "usuario123", "padre")
        except PermissionError:
            pytest.fail("El padre debería poder anular su propia venta")

    def test_padre_ajeno_raise_permission_error(self):
        with pytest.raises(PermissionError):
            verificar_anulacion_venta("usuario123", "otro_usuario", "padre")

    def test_admin_cualquiera_pasa(self):
        try:
            verificar_anulacion_venta("usuario123", "otro_usuario", "administrador")
        except PermissionError:
            pytest.fail("El admin debería poder anular cualquier venta")

    def test_propietario_cualquiera_pasa(self):
        try:
            verificar_anulacion_venta("usuario123", "otro_usuario", "propietario")
        except PermissionError:
            pytest.fail("El propietario debería poder anular cualquier venta")