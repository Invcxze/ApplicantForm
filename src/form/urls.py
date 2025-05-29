from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    DynamicFormListView,
    DynamicFormDetailView,
    DynamicFormSubmissionView,
    FormSubmissionSuccessView,
    RegisterView,
    FormSubmissionDetailView,
    FormSubmissionUpdateView,
    AdminSubmissionListView,
    AdminSubmissionDetailView,
)

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("", DynamicFormListView.as_view(), name="form_list"),
    path("form/<int:pk>/", DynamicFormDetailView.as_view(), name="form_detail"),
    path("form/<int:pk>/submit/", DynamicFormSubmissionView.as_view(), name="form_submit"),
    path("submission/<int:pk>/success/", FormSubmissionSuccessView.as_view(), name="form_success"),
    path("submissions/<int:pk>/", FormSubmissionDetailView.as_view(), name="form_submission_detail"),
    path("submissions/<int:pk>/edit/", FormSubmissionUpdateView.as_view(), name="form_submission_edit"),
    path("admins/submissions/", AdminSubmissionListView.as_view(), name="admin_submission_list"),
    path("admins/submissions/<int:pk>/", AdminSubmissionDetailView.as_view(), name="admin_submission_detail"),
]