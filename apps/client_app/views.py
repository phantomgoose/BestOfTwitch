# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views import View
from .formgen import getStream, getStreamID, getStreamUptime, getStreamFPS, getStreamOffset, clipStream
from django.shortcuts import render, HttpResponse, reverse, redirect

class ClientIndex(View):
    def get(self, request):
        stream = getStream('shroud')
        context = {
            'stream': 'shroud',
            'stream_id': getStreamID(stream),
            'offset': getStreamOffset(stream),
        }

        return render(request, 'client_app/index.html', context)

    def post(self, request):
        clipStream('shroud')
        return redirect(reverse('client-index'))