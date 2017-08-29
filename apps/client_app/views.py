# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.views import View
from ..chat_app.connection import chatStats
from ..clips_app.clipgen import getStreamUptime, getStreamID, getStream, clipStream, updateEmoticonDB
from django.shortcuts import render, HttpResponse, reverse, redirect
from ..clips_app.models import Emoticon

class ClientIndex(View):
    def get(self, request):
        Emoticon.objects.all().delete()
        updateEmoticonDB()
        return render(request, 'client_app/index.html')

    def post(self, request):
        chatStats(request.POST['stream_name'])
        # clipStream('shrodrdisrespectliveud')
        return redirect(reverse('client-index'))