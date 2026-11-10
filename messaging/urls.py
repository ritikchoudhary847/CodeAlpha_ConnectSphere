
from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    path("", views.inbox_view, name="inbox"),
    path("new/<str:username>/", views.start_conversation_view, name="start"),
    path("<int:conversation_id>/", views.conversation_view, name="conversation"),
]
