from django.contrib import admin
from django.db import models
from django.http import FileResponse
from django.urls import reverse, path
from django.utils.html import format_html
from django.contrib.auth.models import User
from django_json_widget.widgets import JSONEditorWidget
from django_admin_relation_links import AdminChangeLinksMixin

from .exporter import FormSubmissionExporter
from .models import FileValue, FormSubmission, FieldValue, FormField, DynamicForm


class FormFieldInline(admin.StackedInline):
    model = FormField
    extra = 0
    ordering = ("order",)
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    fieldsets = (
        (None, {"fields": ("label", "field_type", "order")}),
        (
            "Настройки",
            {"classes": ("collapse",), "fields": ("required", "is_locked", "is_hidden", "choices", "config")},
        ),
    )


@admin.register(DynamicForm)
class DynamicFormAdmin(AdminChangeLinksMixin, admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at", "fields_link", "submissions_link")
    search_fields = ("name",)
    list_filter = ("created_at", "updated_at")
    inlines = [FormFieldInline]
    ordering = ("-updated_at",)
    save_on_top = True
    change_links = ["fields_link", "submissions_link"]

    def fields_link(self, obj):
        count = obj.fields.count()
        url = reverse("admin:form_formfield_changelist") + f"?form__id__exact={obj.id}"
        return format_html('<a href="{}">{} полей</a>', url, count)

    fields_link.short_description = "Поля"

    def submissions_link(self, obj):
        url = reverse("admin:form_export_submissions", args=[obj.id])
        return format_html(
            '<a href="{}">📥 Скачать все</a> | <a href="{}?form__id__exact={}">{} отправок</a>',
            url,
            reverse("admin:form_formsubmission_changelist"),
            obj.id,
            obj.submissions.count(),
        )

    submissions_link.short_description = "Отправки"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:form_id>/export-submissions/",
                self.admin_site.admin_view(self.export_submissions),
                name="form_export_submissions",
            ),
        ]
        return custom_urls + urls

    def export_submissions(self, request, form_id):
        form = self.get_object(request, form_id)
        submissions = form.submissions.all()
        exporter = FormSubmissionExporter()
        zip_file = exporter.export_submissions_to_zip(submissions)
        return FileResponse(zip_file, as_attachment=True, filename=f"{form.name}_submissions.zip")


@admin.register(FormField)
class FormFieldAdmin(AdminChangeLinksMixin, admin.ModelAdmin):
    list_display = ("form_link", "label", "field_type", "required", "order")
    list_filter = ("form", "field_type", "required", "is_locked", "is_hidden")
    search_fields = ("label", "form__name")
    autocomplete_fields = ("form",)
    list_editable = ("order",)
    list_select_related = ("form",)
    formfield_overrides = {
        models.JSONField: {"widget": JSONEditorWidget},
    }
    fieldsets = (
        (None, {"fields": ("form", "label", "field_type")}),
        ("Валидация", {"fields": ("required", "is_locked", "is_hidden")}),
        ("Конфигурация", {"classes": ("collapse",), "fields": ("choices", "config", "order")}),
    )

    def form_link(self, obj):
        url = reverse("admin:form_dynamicform_change", args=[obj.form.id])
        return format_html('<a href="{}">{}</a>', url, obj.form.name)

    form_link.short_description = "Форма"


class FieldValueInline(admin.TabularInline):
    model = FieldValue
    extra = 0
    readonly_fields = ("field_preview", "files_preview")
    fields = ("field_preview", "text_value", "choice_value")
    autocomplete_fields = ("field",)

    def field_preview(self, obj):
        return f"{obj.field.label} ({obj.field.get_field_type_display()})"

    field_preview.short_description = "Поле"

    def files_preview(self, obj):
        return format_html("<br>".join(f'<a href="{fv.file.url}">{fv.file.name}</a>' for fv in obj.files.all()))

    files_preview.short_description = "Файлы"


@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "form_link", "user_link", "submitted_at", "session_preview")
    list_filter = ("form", "submitted_at", ("user", admin.RelatedOnlyFieldListFilter))
    search_fields = ("user__username", "session_key", "form__name")
    readonly_fields = ("submitted_at", "session_key")
    inlines = (FieldValueInline,)
    date_hierarchy = "submitted_at"
    list_select_related = ("form", "user")

    def form_link(self, obj):
        url = reverse("admin:form_dynamicform_change", args=[obj.form.id])
        return format_html('<a href="{}">{}</a>', url, obj.form.name)

    form_link.short_description = "Форма"

    def user_link(self, obj):
        if not obj.user:
            return "Аноним"
        url = reverse("admin:auth_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)

    user_link.short_description = "Пользователь"

    def session_preview(self, obj):
        return obj.session_key[:15] + "..." if obj.session_key else ""

    session_preview.short_description = "Сессия"


class FileValueAdmin(admin.ModelAdmin):
    list_display = ("id", "file_name", "submission_link", "is_image", "uploaded_at")
    list_filter = ("is_image", "uploaded_at")
    search_fields = ("file", "field_value__submission__id")
    readonly_fields = ("file_preview", "uploaded_at")
    date_hierarchy = "uploaded_at"

    def file_name(self, obj):
        return obj.file.name.split("/")[-1]

    def submission_link(self, obj):
        url = reverse("admin:form_formsubmission_change", args=[obj.field_value.submission.id])
        return format_html('<a href="{}">Отправка #{}</a>', url, obj.field_value.submission.id)

    submission_link.short_description = "Отправка"

    def file_preview(self, obj):
        if obj.is_image:
            return format_html('<img src="{}" style="max-height: 200px;" />', obj.file.url)
        return format_html('<a href="{}">Скачать файл</a>', obj.file.url)

    file_preview.allow_tags = True
    file_preview.short_description = "Превью"


admin.site.register(FileValue, FileValueAdmin)


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "submissions_count")
    search_fields = ("username", "email")
    list_filter = ("is_staff", "is_superuser", "is_active")

    def submissions_count(self, obj):
        return obj.formsubmission_set.count()

    submissions_count.short_description = "Отправок форм"


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)