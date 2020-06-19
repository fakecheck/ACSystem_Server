from ACSystemControl.models import Record, AC
from django.utils import timezone

_AC = AC.objects.create(status="on", mode=0, speed=1, roomNumber=2,
                        targetTemperature=25, currentTemperature=25)
Record.objects.create(ac=_AC, old_mode=0, new_mode=1, old_speed=1,
                      new_speed=2, date=timezone.now())
