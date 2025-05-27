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


class DynamicFormDetailView(DetailView):
    model = DynamicForm
    template_name = "forms/form_detail.html"
    context_object_name = "form"


class DynamicFormSubmissionView(View):
    template_name = "forms/form_submit.html"

    def get_form_class(self, dynamic_form):
        fields = {}
        for field in dynamic_form.fields.all():
            field_kwargs = {
                "label": field.label,
                "required": field.required,
            }

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
            submission = FormSubmission.objects.create(
                form=dynamic_form,
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key or "",
            )
            for field in dynamic_form.fields.all():
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

            return redirect("form_success", pk=submission.pk)

        return render(request, self.template_name, {"form": form, "dynamic_form": dynamic_form})


class FormSubmissionSuccessView(DetailView):
    model = FormSubmission
    template_name = "forms/form_success.html"
    context_object_name = "submission"
