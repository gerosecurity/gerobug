from django.urls import path
from .views import LogoutForm, ReportFiles, ReportStatusView, ReportUpdateStatus, FormHandler, AdminSetting, OWASPCalculator, ManageRoles, ReviewerDelete, NotificationDelete, RenderDashboardAdmin, ReportDetails, UpdateDetails, AppealDetails, NDADetails, ReportUpdate, ReportDelete

urlpatterns = [
    path("", RenderDashboardAdmin.as_view(), name="dashboard"),
    
    path("report-detail/<str:pk>", ReportDetails.as_view(), name="report_detail"),
    path("report-detail/<str:pk>/edit/", ReportUpdate.as_view(), name="report_edit"),
    path("report-detail/<str:pk>/delete/", ReportDelete.as_view(), name="report_delete"),

    path("update-detail/<str:pk>", UpdateDetails.as_view(), name="update_detail"),
    path("appeal-detail/<str:pk>", AppealDetails.as_view(), name="appeal_detail"),
    path("nda-detail/<str:pk>", NDADetails.as_view(), name="nda_detail"),
    
    path("report-status/<str:id>", ReportStatusView, name="report_status"),
    path("report-detail/<str:id>/move/", ReportUpdateStatus, name="report_updatestatus"),
    
    path("report-files/<str:id>", ReportFiles, name="report_files"),
    path("form-handling/<str:id>/<str:complete>", FormHandler, name="form_handler"),
    path("review-delete/<str:id>", ReviewerDelete,name="reviewer_handler"),
    path("notification-delete/<str:service>", NotificationDelete,name="notification_handler"),
    
    path("setting", AdminSetting, name="setting"),
    path("calculator", OWASPCalculator, name="calculator"),
    path("manage", ManageRoles, name="manage"),
    path("logout/", LogoutForm, name="logout"),
]
