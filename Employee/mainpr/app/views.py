from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import (
    EmployeeCreateForm,
    EmployeeEditForm,
    EmployeeGroupForm,
    NotificationForm,
    ProjectForm,
)
from .models import EmployeeGroup, EmployeeProfile, Notification, Project


def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


admin_required = user_passes_test(is_admin_user, login_url="login")


@login_required
def dashboard(request):
    if is_admin_user(request.user):
        employees = User.objects.filter(is_staff=False, is_superuser=False).select_related(
            "employee_profile", "employee_profile__group"
        )
        groups = EmployeeGroup.objects.prefetch_related("members")
        projects = Project.objects.prefetch_related("assigned_employees", "assigned_groups")
        notifications = Notification.objects.select_related("recipient", "sender")[:20]
        return render(
            request,
            "app/admin_dashboard.html",
            {
                "employees": employees,
                "groups": groups,
                "projects": projects,
                "notifications": notifications,
            },
        )

    # Read-only employee portal
    profile, _ = EmployeeProfile.objects.get_or_create(user=request.user)
    user_group = profile.group

    projects = Project.objects.filter(
        Q(assigned_employees=request.user)
        | (Q(assigned_groups=user_group) if user_group else Q(pk__in=[]))
    ).distinct()

    notifications = Notification.objects.filter(recipient=request.user)

    return render(
        request,
        "app/employee_dashboard.html",
        {
            "profile": profile,
            "user_group": user_group,
            "projects": projects,
            "notifications": notifications,
        },
    )


@admin_required
def add_employee(request):
    if request.method == "POST":
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = User.objects.create_user(
                username=data["username"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                email=data["email"],
                is_staff=False,
                is_superuser=False,
            )
            profile, _ = EmployeeProfile.objects.get_or_create(user=user)
            profile.job_title = data["job_title"]
            profile.department = data["department"]
            profile.phone = data["phone"]
            profile.group = data["group"]
            profile.save()
            messages.success(request, f"Employee '{user.username}' added.")
            return redirect("dashboard")
    else:
        form = EmployeeCreateForm()
    return render(request, "app/form_page.html", {"form": form, "title": "Add Employee"})


@admin_required
def edit_employee(request, user_id):
    employee = get_object_or_404(User, pk=user_id, is_staff=False, is_superuser=False)
    profile, _ = EmployeeProfile.objects.get_or_create(user=employee)

    if request.method == "POST":
        form = EmployeeEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            employee.first_name = data["first_name"]
            employee.last_name = data["last_name"]
            employee.email = data["email"]
            employee.save()

            profile.job_title = data["job_title"]
            profile.department = data["department"]
            profile.phone = data["phone"]
            profile.group = data["group"]
            profile.save()
            messages.success(request, f"Updated details for '{employee.username}'.")
            return redirect("dashboard")
    else:
        form = EmployeeEditForm(
            initial={
                "first_name": employee.first_name,
                "last_name": employee.last_name,
                "email": employee.email,
                "job_title": profile.job_title,
                "department": profile.department,
                "phone": profile.phone,
                "group": profile.group,
            }
        )
    return render(
        request,
        "app/form_page.html",
        {"form": form, "title": f"Edit Employee: {employee.username}"},
    )


@admin_required
def delete_employee(request, user_id):
    employee = get_object_or_404(User, pk=user_id, is_staff=False, is_superuser=False)
    if request.method == "POST":
        username = employee.username
        employee.delete()
        messages.success(request, f"Employee '{username}' deleted.")
        return redirect("dashboard")
    return render(
        request,
        "app/confirm_delete.html",
        {"object_name": f"employee '{employee.username}'"},
    )


@admin_required
def create_group(request):
    if request.method == "POST":
        form = EmployeeGroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee group created.")
            return redirect("dashboard")
    else:
        form = EmployeeGroupForm()
    return render(request, "app/form_page.html", {"form": form, "title": "Create Employee Group"})


@admin_required
def edit_group(request, group_id):
    group = get_object_or_404(EmployeeGroup, pk=group_id)
    if request.method == "POST":
        form = EmployeeGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated group '{group.name}'.")
            return redirect("dashboard")
    else:
        form = EmployeeGroupForm(instance=group)
    return render(
        request, "app/form_page.html", {"form": form, "title": f"Edit Group: {group.name}"}
    )


@admin_required
def create_project(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Project created and assigned.")
            return redirect("dashboard")
    else:
        form = ProjectForm()
    return render(
        request, "app/form_page.html", {"form": form, "title": "Create & Assign Project"}
    )


@admin_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated project '{project.title}'.")
            return redirect("dashboard")
    else:
        form = ProjectForm(instance=project)
    return render(
        request,
        "app/form_page.html",
        {"form": form, "title": f"Edit / Assign Project: {project.title}"},
    )


@admin_required
def send_notification(request):
    if request.method == "POST":
        form = NotificationForm(request.POST)
        if form.is_valid():
            notif = form.save(commit=False)
            notif.sender = request.user
            notif.save()
            messages.success(request, f"Notification sent to {notif.recipient.username}.")
            return redirect("dashboard")
    else:
        form = NotificationForm()
    return render(request, "app/form_page.html", {"form": form, "title": "Send Notification"})