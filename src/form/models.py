from django.contrib.auth.models import User
from django.db import models
from django.db.models import JSONField
from simple_history.models import HistoricalRecords

from config.storages import MinIOMediaStorage

class DynamicForm(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Динамическая форма"
        verbose_name_plural = "Динамические формы"


class FormField(models.Model):
    FIELD_TYPES = (
        ("text", "Short Text"),
        ("textarea", "Long Text"),
        ("select", "Dropdown"),
        ("checkbox", "Multiple Choice"),
        ("file", "File Upload"),
        ("image", "Image Upload"),
    )

    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE, related_name="fields")
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    required = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    choices = JSONField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    config = JSONField(blank=True, null=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Поле формы"
        verbose_name_plural = "Поля форм"

    def __str__(self):
        return f"{self.form.name} - {self.label}"


class FormSubmission(models.Model):
    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE, related_name="submissions")
    submitted_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Аутентифицированный пользователь",
    )
    session_key = models.CharField(max_length=40, blank=True, db_index=True, verbose_name="Ключ сессии")
    history = HistoricalRecords()

    class Meta:
        unique_together = (("user", "session_key"),)
        verbose_name = "Данные формы пользователя"
        verbose_name_plural = "Данные форм пользователей"

    def __str__(self):
        return f"{self.form.name} - {self.submitted_at}"

    def save(self, *args, **kwargs):
        if self.user:
            self.session_key = ""
        super().save(*args, **kwargs)


class FieldValue(models.Model):
    submission = models.ForeignKey(FormSubmission, on_delete=models.CASCADE, related_name="values")
    field = models.ForeignKey(FormField, on_delete=models.CASCADE)
    text_value = models.TextField(blank=True, null=True)
    choice_value = models.JSONField(blank=True, null=True)

    @property
    def files(self):
        return self.file_values.all()

    def __str__(self):
        return f"{self.field.label} - {self.submission}"

    class Meta:
        verbose_name = "Ответ из формы"
        verbose_name_plural = "Ответы из форм"


class FileValue(models.Model):
    field_value = models.ForeignKey(FieldValue, on_delete=models.CASCADE, related_name="file_values")
    file = models.FileField(upload_to="forms/%Y/%m/%d/",  null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    caption = models.CharField(max_length=255, blank=True)
    is_image = models.BooleanField(default=False)

    def __str__(self):
        return self.file.name

    class Meta:
        verbose_name = "Файл из ответа формы"
        verbose_name_plural = "Файлы из ответов на формы"
