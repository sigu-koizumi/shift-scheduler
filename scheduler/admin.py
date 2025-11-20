from django.contrib import admin
from .models import Staff, ShiftRequest, WorkSchedule

admin.site.register(Staff)
admin.site.register(ShiftRequest)
admin.site.register(WorkSchedule)