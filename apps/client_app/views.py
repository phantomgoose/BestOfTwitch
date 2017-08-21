# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views import View
from .formgen import getStream, getStreamID, getStreamUptime
from django.shortcuts import render, HttpResponse, reverse, redirect

class ClientIndex(View):
    def get(self, request):
        return render(request, 'client_app/index.html')

    def post(self, request):
        stream = getStream('reckful')
        context = {
            'channel_id': getStreamID(stream),
            'created_at': getStreamUptime(stream),
        }
        return redirect(reverse('client-index'))