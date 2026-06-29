from django.urls import path

from .views import (
    AdminResetDataView,
    AdminSeedView,
    AdminStatsView,
    AdminUserDetailView,
    AdminUserListView,
    AdminUserResendVerificationView,
    LLMConfigAdminView,
    SiteConfigAdminView,
)

# Routes /api/admin/... (toutes réservées IsAdminUser)
urlpatterns = [
    path("stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("site-config/", SiteConfigAdminView.as_view(), name="admin-site-config"),
    path("llm-config/", LLMConfigAdminView.as_view(), name="admin-llm-config"),
    path("users/", AdminUserListView.as_view(), name="admin-users"),
    path("users/<int:pk>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path(
        "users/<int:pk>/resend-verification/",
        AdminUserResendVerificationView.as_view(),
        name="admin-user-resend",
    ),
    path("seed/", AdminSeedView.as_view(), name="admin-seed"),
    path("reset-data/", AdminResetDataView.as_view(), name="admin-reset-data"),
]
