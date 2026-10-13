from django.urls import include, path

urlpatterns = [path("", include("catalog.urls"))]

handler404 = "catalog.views.page_not_found"
handler500 = "catalog.views.server_error"
