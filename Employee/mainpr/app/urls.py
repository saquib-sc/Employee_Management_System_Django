from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("employees/add/", views.add_employee, name="add_employee"),
    path("employees/<int:user_id>/edit/", views.edit_employee, name="edit_employee"),
    path("employees/<int:user_id>/delete/", views.delete_employee, name="delete_employee"),
    path("groups/add/", views.create_group, name="create_group"),
    path("groups/<int:group_id>/edit/", views.edit_group, name="edit_group"),
    path("projects/add/", views.create_project, name="create_project"),
    path("projects/<int:project_id>/edit/", views.edit_project, name="edit_project"),
    path("notifications/send/", views.send_notification, name="send_notification"),
]