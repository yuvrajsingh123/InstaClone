# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from forms import SignUpForm, LoginForm, PostForm, LikeForm, CommentForm, UpvoteForm,SearchForm
from models import UserModel, SessionToken, PostModel, LikeModel, CommentModel
from django.contrib.auth.hashers import make_password, check_password
from datetime import timedelta
from django.utils import timezone
from Insta_Clone.settings import BASE_DIR
import requests
from clarifai.rest import ClarifaiApp, Image as CImage
from imgurpython import ImgurClient
from enum import Enum
import sendgrid
from sendgrid.helpers.mail import *
import os


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            # saving data to DB
            user = UserModel(name=name, password=make_password(password), email=email, username=username)
            user.save()
            return render(request, 'success.html')
            # return redirect('login/')
    else:
        form = SignUpForm()

    return render(request, 'index.html', {'form': form})

# create view for login
def login_view(request):
    response_data = {}
    if request.method == "POST":
        form = LoginForm(request.POST)
        # check if form is valid
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = UserModel.objects.filter(username=username).first()

            if user:
                if check_password(password, user.password):
                    token = SessionToken(user=user)
                    token.create_token()

                    # saving session token
                    token.save()
                    response = redirect('feed/')
                    response.set_cookie(key='session_token', value=token.session_token)
                    return response
                else:
                    response_data['message'] = 'Incorrect Password! Please try again!'

    elif request.method == 'GET':
        form = LoginForm()

    response_data['form'] = form
    return render(request, 'login.html', response_data)


# Swach Bharat Objective covered here
# create view for post
def post_view(request):
    user = check_validation(request)

    if user:
        if request.method == 'POST':
            form = PostForm(request.POST, request.FILES)
            #checking if form is valid or not
            if form.is_valid():
                image = form.cleaned_data.get('image')
                caption = form.cleaned_data.get('caption')
                post = PostModel(user=user, image=image, caption=caption)
                #saving posts
                post.save()

                apikey = 'lBzto9IhYQnI8Z6kd4dFap0gGbFexBgRBknxuISGFK4'
                request_url = ('https://apis.paralleldots.com/sentiment?sentence1=%s&apikey=%s') % (caption, apikey)
                print 'POST request url : %s' % (request_url)
                sentiment = requests.get(request_url, verify=False).json()
                sentiment_value = sentiment['sentiment']

                path = str(BASE_DIR + '\\' + post.image.url)

                #imgur api key
                client = ImgurClient("315c0833408f9c0", "ab94bfdc68d430ac6f7aa5f16260b1f5d6e27b5e")
                post.image_url = client.upload_from_path(path, anon=True)['link']
                print post.image_url
                post.save()

                #keywords that will be helpful in accessing dirty area post
                keywords = ['garbage', 'waste', 'trash', 'dirt', 'pollution', 'dust']
                value_list = []
                app = ClarifaiApp(api_key='ecc5aea7265040b4b320b3446f96152c')

                model = app.models.get('general-v1.3')
                image = CImage(url=post.image_url)
                prediction = model.predict([image])

                for i in range(0, len(prediction['outputs'][0]['data']['concepts'])):
                    if prediction['outputs'][0]['data']['concepts'][i]['name'] in keywords:
                        value = prediction['outputs'][0]['data']['concepts'][i]['value']
                        value_list.append(value)
                    #
                        # checking condition
                if (sentiment_value < 0.6 and max(value_list) > 0.8):
                    print 'dirty image'
                    send_mail(post.image_url)

                return redirect('/feed/')

        else:
            form = PostForm()

            #return post html page
        return render(request, 'post.html', {'form': form})
    else:
        return redirect('/login/')

#function for sending email using sendgrid
def send_mail(url):

    #sendgrid api key
    sg = sendgrid.SendGridAPIClient(apikey='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')

    from_email = Email("yuvi0622@gmail.com")
    to_email = Email("ysyuvraj079@gmail.com")
    message = "<html><body><h1>Image of the dirty area</h1><br><img src =" + url + "></body></html>"
    subject = "Image of dirty area!"
    content = Content("text/html", message)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)


#function for feed
def feed_view(request):
    user = check_validation(request)

    #checking a user
    if user:

        posts = PostModel.objects.all().order_by('created_on')

        for post in posts:
            existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first()
            if existing_like:
                post.has_liked = True

        return render(request, 'feed.html', {'posts': posts})
    else:
#return to login page
        return redirect('/login/')

#function for like
def like_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = LikeForm(request.POST)

        #checking whether form is valid or not
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()
            if not existing_like:
                LikeModel.objects.create(post_id=post_id, user=user)
            else:
                existing_like.delete()
            return redirect('/feed/')
    else:
        return redirect('/login/')


#function for comment
def comment_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            comment_text = form.cleaned_data.get('comment_text')
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)

            #saving comment
            comment.save()
            return redirect('/feed/')
        else:
            #redirecting to a feed page
            return redirect('/feed/')
    else:
        return redirect('/login')

#Implement the logout functionality- objective
#function for logout
def logout_view(request):
    user = check_validation(request)
    if user is not None:
        latest_session = SessionToken.objects.filter(user=user).last()
        if latest_session:
            latest_session.delete()

    return redirect("/login/")

# Implement upvoting on a comment -objective
# method to create upvote for comments
def upvote_view(request):
    user = check_validation(request)
    comment = None

    print ("upvote view")
    if user and request.method == 'POST':

        form = UpvoteForm(request.POST)
        if form.is_valid():

            comment_id = int(form.cleaned_data.get('id'))

            comment = CommentModel.objects.filter(id=comment_id).first()
            print ("upvoted not yet")

            if comment is not None:
                # print ' unliking post'
                print ("upvoted")
                comment.upvote_num =+1
                comment.save()
                print (comment.upvote_num)
            else:
                print ('stupid mistake')
                #liked_msg = 'Unliked!'

        return redirect('/feed/')
    else:
        return redirect('/feed/')

# For validating the session
def check_validation(request):
    if request.COOKIES.get('session_token'):
        session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
        if session:
            time_to_live = session.created_on + timedelta(days=1)
            if time_to_live > timezone.now():
                return session.user
    else:
        return None

# Make the url accept query parameters to optionally show posts only from a particular user- objective
#function for query based search... you can search by name
def query_based_search_view(request):
    user = check_validation(request)
    if user:
        if request.method == "POST":
            searchForm = SearchForm(request.POST)

            #checking whether searchform is valid or not
            if searchForm.is_valid():
                print 'valid'
                username_query = searchForm.cleaned_data.get('searchquery')
                user_with_query = UserModel.objects.filter(username=username_query).first();
                posts = PostModel.objects.filter(user=user_with_query)
                return render(request, 'feed.html', {'posts': posts})
            else:
                return redirect('/feed/')
    else:
        return redirect('/login/')