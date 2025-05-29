from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, FormView
from django.shortcuts import get_object_or_404, redirect, render
from .models import DynamicForm, FormSubmission, FieldValue, FileValue
from django.forms import Form, CharField, ChoiceField, MultipleChoiceField, FileField, Textarea
from django.forms import CheckboxSelectMultiple, Select


class RegisterView(FormView):
    template_name = "registration/register.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class DynamicFormListView(ListView):
    model = DynamicForm
    template_name = "forms/form_list.html"
    context_object_name = "forms"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            finished_submissions = FormSubmission.objects.filter(user=user).select_related("form")
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            finished_submissions = FormSubmission.objects.filter(session_key=session_key).select_related("form")

        context["finished_submissions"] = finished_submissions
        return context


class DynamicFormDetailView(DetailView):
    model = DynamicForm
    template_name = "forms/form_detail.html"
    context_object_name = "form"


class DynamicFormSubmissionView(View):
    template_name = "forms/form_submit.html"

    def get_form_class(self, dynamic_form, submission=None):
        fields = {}
        for field in dynamic_form.fields.all():
            if field.is_hidden:
                continue

            field_kwargs = {
                "label": field.label,
                "required": field.required,
            }

            if field.is_locked:
                field_kwargs["disabled"] = True

            if field.field_type == "text":
                fields[field.label] = CharField(**field_kwargs)
            elif field.field_type == "textarea":
                field_kwargs["widget"] = Textarea
                fields[field.label] = CharField(**field_kwargs)
            elif field.field_type == "select":
                field_kwargs["widget"] = Select
                field_kwargs["choices"] = [(c, c) for c in field.choices or []]
                fields[field.label] = ChoiceField(**field_kwargs)
            elif field.field_type == "checkbox":
                field_kwargs["widget"] = CheckboxSelectMultiple
                field_kwargs["choices"] = [(c, c) for c in field.choices or []]
                fields[field.label] = MultipleChoiceField(**field_kwargs)
            elif field.field_type in ["file", "image"]:
                fields[field.label] = FileField(**field_kwargs)

        return type("DynamicForm", (Form,), fields)

    def get(self, request, pk):
        dynamic_form = get_object_or_404(DynamicForm, pk=pk)
        form_class = self.get_form_class(dynamic_form)
        form = form_class()
        return render(request, self.template_name, {"form": form, "dynamic_form": dynamic_form})

    def post(self, request, pk):
        dynamic_form = get_object_or_404(DynamicForm, pk=pk)
        form_class = self.get_form_class(dynamic_form)
        form = form_class(request.POST, request.FILES)

        if form.is_valid():
            if request.user.is_authenticated:
                submission = FormSubmission.objects.create(form=dynamic_form, user=request.user)
            else:
                session_key = request.session.session_key
                if not session_key:
                    request.session.create()
                    session_key = request.session.session_key
                submission = FormSubmission.objects.create(form=dynamic_form, session_key=session_key)

            for field in dynamic_form.fields.all():
                if field.is_hidden:
                    continue

                value = form.cleaned_data.get(field.label)
                if field.field_type in ["file", "image"]:
                    field_value = FieldValue.objects.create(submission=submission, field=field)
                    for uploaded_file in request.FILES.getlist(field.label):
                        FileValue.objects.create(
                            field_value=field_value, file=uploaded_file, is_image=(field.field_type == "image")
                        )
                elif field.field_type == "checkbox":
                    FieldValue.objects.create(submission=submission, field=field, choice_value=value)
                elif field.field_type == "select":
                    FieldValue.objects.create(submission=submission, field=field, choice_value=[value])
                else:
                    FieldValue.objects.create(submission=submission, field=field, text_value=value)

            return redirect("form_submission_detail", pk=submission.pk)

        return render(request, self.template_name, {"form": form, "dynamic_form": dynamic_form})


class FormSubmissionSuccessView(DetailView):
    model = FormSubmission
    template_name = "forms/form_success.html"
    context_object_name = "submission"


class FormSubmissionDetailView(DetailView):
    model = FormSubmission
    template_name = "forms/form_submission_detail.html"
    context_object_name = "submission"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["field_values"] = FieldValue.objects.filter(submission=self.object).select_related("field")
        context["file_values"] = FileValue.objects.filter(field_value__submission=self.object)
        return context


class FormSubmissionUpdateView(View):
    template_name = "forms/form_edit.html"

    def get_form_class(self, submission):
        fields = {}
        for field in submission.form.fields.all():
            if field.is_hidden:
                continue

            field_kwargs = {
                "label": field.label,
                "required": field.required,
            }

            if field.is_locked:
                field_kwargs["disabled"] = True

            if field.field_type == "text":
                fields[field.label] = CharField(**field_kwargs)
            elif field.field_type == "textarea":
                field_kwargs["widget"] = Textarea
                fields[field.label] = CharField(**field_kwargs)
            elif field.field_type == "select":
                field_kwargs["widget"] = Select
                field_kwargs["choices"] = [(c, c) for c in field.choices or []]
                fields[field.label] = ChoiceField(**field_kwargs)
            elif field.field_type == "checkbox":
                field_kwargs["widget"] = CheckboxSelectMultiple
                field_kwargs["choices"] = [(c, c) for c in field.choices or []]
                fields[field.label] = MultipleChoiceField(**field_kwargs)
            elif field.field_type in ["file", "image"]:
                fields[field.label] = FileField(required=False, **field_kwargs)

        return type("DynamicForm", (Form,), fields)

    def get_initial(self, submission):
        initial = {}
        for value in submission.values.all():
            if value.text_value is not None:
                initial[value.field.label] = value.text_value
            elif value.choice_value:
                if value.field.field_type == "checkbox":
                    initial[value.field.label] = value.choice_value
                else:
                    initial[value.field.label] = value.choice_value[0]
        return initial

    def get(self, request, pk):
        submission = get_object_or_404(FormSubmission, pk=pk)
        form_class = self.get_form_class(submission)
        form = form_class(initial=self.get_initial(submission))
        return render(request, self.template_name, {"form": form, "submission": submission})

    def post(self, request, pk):
        submission = get_object_or_404(FormSubmission, pk=pk)
        form_class = self.get_form_class(submission)
        form = form_class(request.POST, request.FILES)

        if form.is_valid():
            for field in submission.form.fields.all():
                if field.is_locked:
                    continue  # 🔒 Игнорируем заблокированные поля

                value = form.cleaned_data.get(field.label)
                existing_value = FieldValue.objects.filter(submission=submission, field=field).first()

                # Удаление, если значение пустое
                if value in [None, "", [], (), {}]:
                    if existing_value:
                        if field.field_type in ["file", "image"]:
                            existing_value.files.all().delete()
                        existing_value.delete()
                    continue

                # Обновление
                if field.field_type in ["file", "image"]:
                    field_value, _ = FieldValue.objects.get_or_create(submission=submission, field=field)
                    field_value.files.all().delete()
                    for uploaded_file in request.FILES.getlist(field.label):
                        FileValue.objects.create(
                            field_value=field_value, file=uploaded_file, is_image=(field.field_type == "image")
                        )

                elif field.field_type == "checkbox":
                    FieldValue.objects.update_or_create(
                        submission=submission,
                        field=field,
                        defaults={"choice_value": value},
                    )

                elif field.field_type == "select":
                    FieldValue.objects.update_or_create(
                        submission=submission,
                        field=field,
                        defaults={"choice_value": [value]},
                    )

                else:
                    FieldValue.objects.update_or_create(
                        submission=submission,
                        field=field,
                        defaults={"text_value": value},
                    )

            return redirect("form_submission_detail", pk=submission.pk)

        return render(request, self.template_name, {"form": form, "submission": submission})
