from django.urls import path
from .views import LogoutForm, ReportFiles, ReportStatusView, ReportUpdateStatus, FormHandler, AdminSetting, OWASPCalculator, RenderDashboardAdmin, ReportDetails, ReportUpdate, ReportDelete

urlpatterns = [
    path("", RenderDashboardAdmin.as_view(), name="dashboard"),
    
    path("report-detail/<str:pk>", ReportDetails.as_view(), name="report_detail"),
    path("report-detail/<str:pk>/edit/", ReportUpdate.as_view(), name="report_edit"),
    path("report-detail/<str:pk>/delete/", ReportDelete.as_view(), name="report_delete"),
    path("report-status/<str:id>", ReportStatusView, name="report_status"),
    path("report-detail/<str:id>/move/", ReportUpdateStatus, name="report_updatestatus"),
    path("report-files/<str:id>", ReportFiles, name="report_files"),
    path("form-handling/<str:id>/<str:complete>", FormHandler, name="form_handler"),
    path("setting", AdminSetting, name="setting"),
    path("calculator", OWASPCalculator, name="calculator"),
    path("logout/", LogoutForm, name="logout"),
]
