from django.urls import path

from . import ACSystem

urlpatterns = [
    path('startup', ACSystem.startup),
    path('register', ACSystem.register),
    path('checkout', ACSystem.checkout),
    path('checkDetail', ACSystem.checkDetail),
    path('update', ACSystem.update),
    path('hibernate', ACSystem.hibernate),
    path('powerOff', ACSystem.powerOff),
]
