# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views import View
from django.shortcuts import render
from .models import Clip

class ClipContainer(View):
    def get(self, request):
        context = {
            'clips': Clip.objects.all()
        }
        return render(request, 'clips_app/clips_container.html', context)