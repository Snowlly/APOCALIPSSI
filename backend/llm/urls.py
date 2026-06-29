from django.urls import path

from .views import GenerateQuizView, PingView

urlpatterns = [
    path("ping/", PingView.as_view(), name="llm-ping"),
    path("generate-quiz/", GenerateQuizView.as_view(), name="llm-generate-quiz"),
]
