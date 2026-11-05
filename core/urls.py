from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('crear-empresa/', views.crear_empresa, name='crear_empresa'),

    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/nuevo/', views.cliente_crear, name='cliente_crear'),
    path('clientes/<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('clientes/<int:pk>/eliminar/', views.cliente_eliminar, name='cliente_eliminar'),

    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/nuevo/', views.proveedor_crear, name='proveedor_crear'),
    path('proveedores/<int:pk>/editar/', views.proveedor_editar, name='proveedor_editar'),
    path('proveedores/<int:pk>/eliminar/', views.proveedor_eliminar, name='proveedor_eliminar'),

    path('productos/', views.lista_productos, name='lista_productos'),
    path('productos/nuevo/', views.producto_crear, name='producto_crear'),
    path('productos/<int:pk>/editar/', views.producto_editar, name='producto_editar'),
    path('productos/<int:pk>/eliminar/', views.producto_eliminar, name='producto_eliminar'),

    path('ventas/', views.lista_ventas, name='lista_ventas'),
    path('ventas/nuevo/', views.venta_crear, name='venta_crear'),
    path('ventas/<int:pk>/', views.venta_detalle, name='venta_detalle'),
    path('ventas/<int:pk>/anular/', views.venta_anular, name='venta_anular'),

    path('compras/', views.lista_compras, name='lista_compras'),
    path('compras/nuevo/', views.compra_crear, name='compra_crear'),
    path('compras/<int:pk>/', views.compra_detalle, name='compra_detalle'),
    path('compras/<int:pk>/anular/', views.compra_anular, name='compra_anular'),

    path('por-cobrar/', views.lista_por_cobrar, name='lista_por_cobrar'),
    path('por-pagar/', views.lista_por_pagar, name='lista_por_pagar'),
    path('pago/<str:tipo>/<int:pk>/', views.registrar_pago, name='registrar_pago'),

    path('reportes/', views.reporte, name='reporte'),
    path('reportes/exportar-ventas/', views.exportar_ventas_csv, name='exportar_ventas_csv'),
    path('reportes/exportar-compras/', views.exportar_compras_csv, name='exportar_compras_csv'),

    path('trabajadores/', views.lista_trabajadores, name='lista_trabajadores'),
    path('trabajadores/nuevo/', views.trabajador_crear, name='trabajador_crear'),
    path('trabajadores/<int:pk>/editar/', views.trabajador_editar, name='trabajador_editar'),
    path('trabajadores/<int:pk>/eliminar/', views.trabajador_eliminar, name='trabajador_eliminar'),

    path('planilla/', views.lista_planillas, name='lista_planillas'),
    path('planilla/nueva/', views.planilla_crear, name='planilla_crear'),
    path('planilla/<int:pk>/', views.planilla_detalle, name='planilla_detalle'),
    path('planilla/<int:pk>/cerrar/', views.planilla_cerrar, name='planilla_cerrar'),
    path('planilla/<int:pk>/exportar/', views.planilla_export_csv, name='planilla_export_csv'),
]
