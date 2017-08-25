# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views import View
from ..chat_app.connection import chatStats
from ..clips_app.clipgen import getStreamUptime, getStreamID, getStream, clipStream
from django.shortcuts import render, HttpResponse, reverse, redirect

class ClientIndex(View):
    def get(self, request):
        return render(request, 'client_app/index.html')

    def post(self, request):
        chatStats(request.POST['stream_name'])
        # clipStream('shrodrdisrespectliveud')
        return redirect(reverse('client-index'))